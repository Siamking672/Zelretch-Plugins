"""
Plugin loader — auto-scan with optional manifest.

Combines the strongest features from both source projects:
- Zelretch: glob-based auto-scan + importlib module load + HelpMenu registry
- FoxUserbot: hot load/unload with handler introspection + safe-mode skip

Plugin contract
---------------
A plugin is any Python module placed under a discovered plugins directory
(either ``astralbot/plugins/builtins/`` for always-on core commands, or
``userdata/plugins/`` for user-installed plugins, or any directory specified
by PLUGIN_PATH env).

Each plugin MAY declare module-level manifest attributes (recommended):

    __plugin_name__        = "Admin Tools"          # display name
    __plugin_author__      = "AstralBot Team"
    __plugin_version__     = "1.0.0"
    __plugin_license__     = "GPL-3.0"
    __plugin_description__ = "..."
    __plugin_category__    = "admin"                # admin|utils|media|ai|fun|privacy
    __plugin_deps__        = ["aiohttp"]            # optional pip deps
    __plugin_min_core__    = "1.0.0"                # minimum AstralBot version

If any are missing, defaults are inferred (filename stem, version "0.0",
author "unknown", category "misc"). Plugins without manifests still load —
the manifest is purely informational.

Commands are registered via the ``@on_command`` decorator (see decorator.py),
which fans handlers across every active client. A plugin's help entries are
registered via ``help_menu.add(...)`` calls (see help.py).
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from astralbot import __version__ as CORE_VERSION

if TYPE_CHECKING:
    from pyrogram import Client
    from astralbot.core.config import Config

LOGS = logging.getLogger("astralbot.loader")


@dataclass
class PluginManifest:
    """Metadata discovered for each loaded plugin."""

    name: str
    file: str
    module: object
    version: str = "0.0"
    author: str = "unknown"
    license: str = "GPL-3.0"
    description: str = ""
    category: str = "misc"
    deps: list[str] = field(default_factory=list)
    min_core: str = "0.0"
    status: str = "loaded"  # loaded | disabled | failed
    error: str | None = None


class PluginLoader:
    """Discovers and loads plugins from one or more search roots."""

    def __init__(self, config: "Config", clients: list["Client"]):
        self.config = config
        self.clients = clients
        self.loaded: dict[str, PluginManifest] = {}
        self.search_roots: list[Path] = []
        self._build_search_roots()

    def _build_search_roots(self) -> None:
        # Built-in commands always available
        builtin_root = Path(__file__).resolve().parent.parent / "plugins" / "builtins"
        if builtin_root.exists():
            self.search_roots.append(builtin_root)

        # User-installed plugins (loaded via .install)
        user_root = self.config.data_dir / "plugins"
        user_root.mkdir(parents=True, exist_ok=True)
        self.search_roots.append(user_root)

        # External plugin repo (cloned/updated at startup by updater.py)
        external_root = self.config.data_dir / "external_plugins" / self.config.plugin_path
        if external_root.exists():
            self.search_roots.append(external_root)

    def add_root(self, path: Path | str) -> None:
        p = Path(path)
        if p.exists() and p not in self.search_roots:
            self.search_roots.append(p)

    async def load_all(self, safe_mode: bool = False) -> dict[str, PluginManifest]:
        """Load every plugin from every search root.

        If safe_mode is True (set after a crash on previous boot), only
        builtins are loaded so the user can reach .unloadmod to fix the issue.
        """
        roots = self.search_roots[:1] if safe_mode else self.search_roots
        LOGS.info("Scanning %d plugin root(s) [safe_mode=%s]", len(roots), safe_mode)
        for root in roots:
            await self._scan_root(root)
        return self.loaded

    async def _scan_root(self, root: Path) -> None:
        # Treat each .py file as a plugin; also recurse one level into subdirs
        # (e.g. modules/admin/admins.py — we load .py files in subdirs).
        candidates: list[Path] = []
        for entry in sorted(root.iterdir()):
            if entry.is_file() and entry.suffix == ".py" and not entry.name.startswith("_"):
                candidates.append(entry)
            elif entry.is_dir() and (entry / "__init__.py").exists():
                # Package — load each .py inside (one level deep)
                for sub in sorted(entry.iterdir()):
                    if sub.is_file() and sub.suffix == ".py" and not sub.name.startswith("_"):
                        candidates.append(sub)

        for path in candidates:
            name = path.stem
            if name in self.config.disabled_plugins:
                self.loaded[name] = PluginManifest(
                    name=name, file=str(path), module=None, status="disabled"
                )
                LOGS.info("Plugin '%s' is disabled (DISABLED_PLUGINS).", name)
                continue
            await self.load_one(name, path)

    async def load_one(self, name: str, path: Path) -> PluginManifest | None:
        """Import a single plugin file. Captures errors so one bad plugin
        doesn't break the whole bot."""
        try:
            module = self._import_file(name, path)
        except Exception as exc:
            LOGS.exception("Failed to load plugin '%s' from %s: %s", name, path, exc)
            manifest = PluginManifest(
                name=name, file=str(path), module=None, status="failed", error=str(exc)
            )
            self.loaded[name] = manifest
            return manifest

        manifest = self._extract_manifest(name, path, module)
        self.loaded[name] = manifest
        LOGS.info(
            "Loaded plugin: %s v%s by %s [%s]",
            manifest.name, manifest.version, manifest.author, manifest.category,
        )
        return manifest

    def _import_file(self, name: str, path: Path) -> object:
        """importlib load a .py file as a module. Reloads if already imported."""
        full_name = f"astralbot_plugin_{name}"
        spec = importlib.util.spec_from_file_location(full_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot build spec for {path}")
        module = importlib.util.module_from_spec(spec)

        # If already imported (reload case), remove old handlers first
        if full_name in sys.modules:
            self._unload_handlers(full_name)
            sys.modules.pop(full_name, None)

        sys.modules[full_name] = module
        spec.loader.exec_module(module)
        return module

    def _extract_manifest(self, name: str, path: Path, module: object) -> PluginManifest:
        return PluginManifest(
            name=getattr(module, "__plugin_name__", name),
            file=str(path),
            module=module,
            version=getattr(module, "__plugin_version__", "0.0"),
            author=getattr(module, "__plugin_author__", "unknown"),
            license=getattr(module, "__plugin_license__", "GPL-3.0"),
            description=getattr(module, "__plugin_description__", ""),
            category=getattr(module, "__plugin_category__", "misc"),
            deps=list(getattr(module, "__plugin_deps__", [])),
            min_core=getattr(module, "__plugin_min_core__", "0.0"),
        )

    # ---- Hot load / unload (FoxUserbot-style) ----

    async def unload(self, name: str) -> bool:
        """Remove a plugin's handlers from every client and deregister its
        commands from the help registry."""
        manifest = self.loaded.get(name)
        if not manifest:
            return False

        # Drop handlers — decorator.py keeps a registry of (client, handler, group)
        # tuples per plugin module name. We call into that to remove them.
        from astralbot.plugins.decorator import _remove_handlers_for_plugin
        _remove_handlers_for_plugin(name, self.clients)

        # Deregister help entries
        from astralbot.plugins.help import registry
        registry.remove_module(name)

        # Remove from sys.modules so a subsequent load re-imports cleanly
        full_name = f"astralbot_plugin_{name}"
        sys.modules.pop(full_name, None)

        self.loaded.pop(name, None)
        LOGS.info("Unloaded plugin: %s", name)
        return True

    async def reload(self, name: str) -> PluginManifest | None:
        manifest = self.loaded.get(name)
        if not manifest:
            return None
        path = Path(manifest.file)
        await self.unload(name)
        return await self.load_one(name, path)

    def _unload_handlers(self, full_module_name: str) -> None:
        from astralbot.plugins.decorator import _remove_handlers_for_module
        _remove_handlers_for_module(full_module_name, self.clients)

    # ---- Summary ----

    def status_table(self) -> str:
        if not self.loaded:
            return "No plugins loaded."
        lines = ["<b>Loaded Plugins</b>\n"]
        for m in sorted(self.loaded.values(), key=lambda x: (x.category, x.name)):
            emoji = {"loaded": "✅", "disabled": "⛔", "failed": "❌"}.get(m.status, "❓")
            lines.append(f"{emoji} <code>{m.name}</code> v{m.version} — <i>{m.category}</i>")
        return "\n".join(lines)

"""
Help registry — fluent builder for command help entries.

Combines the best of both source projects:
- Zelretch's ``HelpMenu().add(...).info(...).done()`` fluent builder pattern
- FoxUserbot's auto-generated ``fox_command()`` help registration

Public API::

    from astralbot import help_menu

    help_menu.add(
        command="ping",
        args=None,
        description="Check bot latency.",
        example="ping",
        category="core",
        plugin="ping",
        aliases=["p"],
    ).register()

    # Or chained:
    help_menu.add(command="kick", args="<user>", description="Kick a user", ...) \
             .add(command="ban", args="<user>", description="Ban a user", ...) \
             .register()

The registry is consumed by the ``.help`` builtin command to render an
inline-button menu, and by ``.plinfo`` / ``.cmdinfo`` for textual dumps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

LOGS = logging.getLogger("astralbot.help")


@dataclass
class CommandInfo:
    command: str
    args: str | None = None
    description: str = ""
    example: str | None = None
    note: str | None = None
    category: str = "misc"
    plugin: str = ""
    aliases: list[str] = field(default_factory=list)


@dataclass
class PluginInfo:
    name: str
    file: str = ""
    version: str = "0.0"
    author: str = "unknown"
    license: str = "GPL-3.0"
    description: str = ""
    category: str = "misc"
    commands: list[CommandInfo] = field(default_factory=list)


class HelpRegistry:
    """Global singleton. Access via ``from astralbot import help_menu``."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginInfo] = {}
        self._commands: dict[str, CommandInfo] = {}

    def register_module(
        self,
        name: str,
        *,
        file: str = "",
        version: str = "0.0",
        author: str = "unknown",
        license: str = "GPL-3.0",
        description: str = "",
        category: str = "misc",
    ) -> PluginInfo:
        info = self._plugins.setdefault(name, PluginInfo(name=name))
        info.file = file or info.file
        info.version = version or info.version
        info.author = author or info.author
        info.license = license or info.license
        info.description = description or info.description
        info.category = category or info.category
        return info

    def add(
        self,
        command: str,
        args: str | None = None,
        description: str = "",
        example: str | None = None,
        note: str | None = None,
        category: str = "misc",
        plugin: str = "",
        aliases: list[str] | None = None,
    ) -> "_Chain":
        """Add a command to the registry. Returns a chainable builder.

        The chainable builder is necessary because some plugins register
        multiple commands under one logical group (e.g. ``kick`` / ``dkick``).
        """
        info = CommandInfo(
            command=command,
            args=args,
            description=description,
            example=example or command,
            note=note,
            category=category,
            plugin=plugin,
            aliases=list(aliases or []),
        )
        return _Chain(self, info)

    def remove_module(self, plugin_name: str) -> None:
        info = self._plugins.pop(plugin_name, None)
        if not info:
            return
        for cmd in info.commands:
            self._commands.pop(cmd.command, None)
            for alias in cmd.aliases:
                self._commands.pop(alias, None)

    def all_modules(self) -> dict[str, PluginInfo]:
        return dict(self._plugins)

    def all_commands(self) -> dict[str, CommandInfo]:
        return dict(self._commands)

    def commands_by_category(self) -> dict[str, list[CommandInfo]]:
        out: dict[str, list[CommandInfo]] = {}
        for cmd in self._commands.values():
            out.setdefault(cmd.category, []).append(cmd)
        return out

    def render_help(self, prefix: str = ".") -> str:
        if not self._plugins:
            return "No commands registered."
        lines: list[str] = []
        by_cat = self.commands_by_category()
        # Track commands we've already shown to avoid duplicates across plugins
        shown: set[str] = set()
        for cat in sorted(by_cat):
            lines.append(f"<b>{cat.upper()}</b>")
            for cmd in sorted(by_cat[cat], key=lambda c: c.command):
                if cmd.command in shown:
                    continue
                shown.add(cmd.command)
                args = f" <code>{cmd.args}</code>" if cmd.args else ""
                lines.append(f"  <code>{prefix}{cmd.command}</code>{args} — {cmd.description}")
            lines.append("")
        return "\n".join(lines)

    def render_plugin_list(self) -> str:
        if not self._plugins:
            return "No plugins loaded."
        lines = ["<b>Loaded Plugins</b>\n"]
        for name, info in sorted(self._plugins.items()):
            lines.append(
                f"<b>{name}</b> v{info.version} by <i>{info.author}</i> "
                f"[{info.category}] — {len(info.commands)} commands"
            )
        return "\n".join(lines)


class _Chain:
    """Chainable helper returned by ``help_menu.add(...)``."""

    def __init__(self, registry: HelpRegistry, info: CommandInfo):
        self._registry = registry
        self._infos: list[CommandInfo] = [info]

    def add(self, **kwargs: Any) -> "_Chain":
        """Add another command to this group."""
        # Default plugin/category to the previous entry's
        prev = self._infos[-1]
        kwargs.setdefault("plugin", prev.plugin)
        kwargs.setdefault("category", prev.category)
        info = CommandInfo(
            command=kwargs["command"],
            args=kwargs.get("args"),
            description=kwargs.get("description", ""),
            example=kwargs.get("example") or kwargs["command"],
            note=kwargs.get("note"),
            category=kwargs.get("category", "misc"),
            plugin=kwargs.get("plugin", ""),
            aliases=list(kwargs.get("aliases") or []),
        )
        self._infos.append(info)
        return self

    def info(self, text: str) -> "_Chain":
        """Set the description for the most recently added command."""
        self._infos[-1].description = text
        return self

    def note(self, text: str) -> "_Chain":
        self._infos[-1].note = text
        return self

    def register(self) -> "_Chain":
        """Commit all queued commands to the registry."""
        for info in self._infos:
            # Register command
            self._registry._commands[info.command] = info
            for alias in info.aliases:
                self._registry._commands[alias] = info
            # Attach to plugin
            plugin_name = info.plugin or "misc"
            plugin = self._registry._plugins.setdefault(
                plugin_name, PluginInfo(name=plugin_name, category=info.category)
            )
            # Replace if exists (for reload case)
            existing = next((c for c in plugin.commands if c.command == info.command), None)
            if existing:
                plugin.commands.remove(existing)
            plugin.commands.append(info)
        return self


# Singleton — imported as `registry` by astralbot/__init__.py
registry = HelpRegistry()

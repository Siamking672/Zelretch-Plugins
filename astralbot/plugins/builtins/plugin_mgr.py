"""Plugin manager builtin — load / unload / install / uninstall / list."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path

from astralbot import on_command, help_menu, Config, LOGS

__plugin_name__ = "Plugin Manager"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Load / unload / install / uninstall / list plugins."
__plugin_category__ = "core"


# We hold a single PluginLoader instance per process; access via attribute on
# the function (initialised lazily on first command use).
_LOADER = None


def _get_loader():
    global _LOADER
    if _LOADER is None:
        from astralbot import clients
        from astralbot.core.loader import PluginLoader
        _LOADER = PluginLoader(Config, clients)
        _LOADER._build_search_roots()
    return _LOADER


@on_command("list", description="List all loaded plugins.", permission="sudo")
async def list_cmd(client, message):
    loader = _get_loader()
    text = loader.status_table()
    await message.edit_text(text)


@on_command("load", description="Load a plugin by name (file stem).", permission="owner")
async def load_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}load <name>`")
    name = message.command[1]
    loader = _get_loader()
    # Find the plugin file in any search root
    path = _find_plugin_file(loader, name)
    if not path:
        return await message.edit_text(f"Plugin `{name}` not found in any search root.")
    manifest = await loader.load_one(name, path)
    if manifest.status == "loaded":
        await message.edit_text(f"✅ Loaded `{name}` v{manifest.version} by {manifest.author}")
    else:
        await message.edit_text(f"❌ Failed to load `{name}`: {manifest.error}")


@on_command("unload", description="Unload a plugin by name.", permission="owner")
async def unload_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}unload <name>`")
    name = message.command[1]
    loader = _get_loader()
    ok = await loader.unload(name)
    if ok:
        await message.edit_text(f"✅ Unloaded `{name}`")
    else:
        await message.edit_text(f"❌ Plugin `{name}` is not loaded.")


@on_command("reload", description="Reload a plugin by name.", permission="owner")
async def reload_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}reload <name>`")
    name = message.command[1]
    loader = _get_loader()
    manifest = await loader.reload(name)
    if manifest and manifest.status == "loaded":
        await message.edit_text(f"✅ Reloaded `{name}` v{manifest.version}")
    else:
        err = manifest.error if manifest else "not loaded"
        await message.edit_text(f"❌ Failed to reload `{name}`: {err}")


@on_command("install", description="Install a plugin from a replied .py file.", permission="owner")
async def install_cmd(client, message):
    target = message.reply_to_message
    if not target or not (target.document or target.video or target.photo):
        return await message.edit_text(
            f"Reply to a `.py` file with `{Config.primary_prefix}install <name>`"
        )
    if len(message.command) < 2:
        return await message.edit_text(f"Provide a name: `{Config.primary_prefix}install <name>`")
    name = message.command[1]
    if not name.endswith(".py"):
        name = name + ".py"
    name = name.replace(".py", "") + ".py" if not name.endswith(".py") else name

    # Sanitize
    safe_name = "".join(c for c in name if c.isalnum() or c in "._-")
    if not safe_name.endswith(".py"):
        safe_name += ".py"
    dest = Config.data_dir / "plugins" / safe_name
    dest.parent.mkdir(parents=True, exist_ok=True)

    msg = await message.edit_text(f"⬇️ Downloading `{safe_name}`...")
    try:
        path = await client.download_media(target, file_name=str(dest))
    except Exception as exc:
        return await msg.edit_text(f"❌ Download failed: {exc}")
    if not path:
        return await msg.edit_text("❌ Download failed (no path returned).")

    # Load it
    loader = _get_loader()
    stem = Path(safe_name).stem
    manifest = await loader.load_one(stem, Path(path))
    if manifest.status == "loaded":
        await msg.edit_text(f"✅ Installed `{stem}` v{manifest.version} by {manifest.author}")
    else:
        # Delete the bad file
        Path(path).unlink(missing_ok=True)
        await msg.edit_text(f"❌ Install failed: {manifest.error}")


@on_command("uninstall", description="Uninstall a plugin (delete the file).", permission="owner")
async def uninstall_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}uninstall <name>`")
    name = message.command[1]
    loader = _get_loader()
    await loader.unload(name)
    # Find and delete the file
    path = _find_plugin_file(loader, name)
    if path:
        try:
            Path(path).unlink()
            await message.edit_text(f"✅ Uninstalled `{name}` (deleted {path})")
        except Exception as exc:
            await message.edit_text(f"❌ Failed to delete file: {exc}")
    else:
        await message.edit_text(f"⚠️ Unloaded `{name}` but no file found to delete.")


def _find_plugin_file(loader, name: str) -> Path | None:
    for root in loader.search_roots:
        candidate = root / f"{name}.py"
        if candidate.exists():
            return candidate
        # Check subdirs (one level deep)
        for sub in root.iterdir():
            if sub.is_dir():
                candidate = sub / f"{name}.py"
                if candidate.exists():
                    return candidate
    return None


# Register help entries
for cmd, desc, ex in [
    ("list", "List all loaded plugins.", ".list"),
    ("load", "Load a plugin by name.", ".load ping"),
    ("unload", "Unload a plugin by name.", ".unload ping"),
    ("reload", "Reload a plugin by name.", ".reload ping"),
    ("install", "Install a plugin from a replied .py file.", ".install myplugin (reply to file)"),
    ("uninstall", "Uninstall a plugin (deletes its file).", ".uninstall myplugin"),
]:
    help_menu.add(
        command=cmd,
        description=desc,
        example=ex,
        category="core",
        plugin="plugin_mgr",
    ).register()

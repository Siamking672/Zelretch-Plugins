"""Config builtin — get / set runtime env vars (DB-backed)."""

from __future__ import annotations

import json

from astralbot import on_command, help_menu, Config, db

__plugin_name__ = "Config"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Read / set / delete runtime config vars."
__plugin_category__ = "core"


@on_command(["getvar", "gv"], description="Read a runtime config var.", permission="owner")
async def getvar_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}getvar <key>`")
    key = message.command[1]
    value = await db.get_env(key, default=None)
    if value is None:
        return await message.edit_text(f"🔑 `{key}` is not set.")
    await message.edit_text(f"🔑 `{key}` = `{json.dumps(value) if not isinstance(value, str) else value}`")


@on_command(["setvar", "sv"], description="Set a runtime config var.", permission="owner")
async def setvar_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 2)
    if len(parts) < 3:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}setvar <key> <value>`")
    key = parts[1]
    value = parts[2]
    # Try to parse as JSON for typed values
    try:
        value_parsed = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        value_parsed = value
    await db.set_env(key, value_parsed)
    await message.edit_text(f"✅ `{key}` = `{value}`")


@on_command(["delvar", "dv"], description="Delete a runtime config var.", permission="owner")
async def delvar_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}delvar <key>`")
    key = message.command[1]
    await db.del_env(key)
    await message.edit_text(f"🗑️ Deleted `{key}`")


@on_command(["listvar", "lv"], description="List all runtime config vars.", permission="owner")
async def listvar_cmd(client, message):
    env = await db.list_env()
    if not env:
        return await message.edit_text("No runtime config vars set.")
    lines = ["**Runtime config vars:**\n"]
    for k, v in sorted(env.items()):
        v_str = json.dumps(v) if not isinstance(v, str) else v
        if len(v_str) > 80:
            v_str = v_str[:77] + "..."
        lines.append(f"  `{k}` = `{v_str}`")
    text = "\n".join(lines)
    if len(text) > 4096:
        # Send as a .txt document — no external paste service dependency
        from astralbot.plugins.builtins.help_cmd import _send_long_text
        await message.edit_text("📋 Too many vars — sending as a document...")
        await _send_long_text(
            message,
            text,
            filename="astralbot-vars.txt",
            caption="📋 AstralBot runtime config vars",
        )
        return
    await message.edit_text(text)


@on_command("prefix", description="Show current command prefixes.", permission="sudo")
async def prefix_cmd(client, message):
    await message.edit_text(
        f"Current prefixes: `{'`, `'.join(Config.handlers)}`\n"
        f"Primary: `{Config.primary_prefix}`"
    )


# Register help
for cmd, desc, ex in [
    ("getvar", "Read a runtime config var.", ".getvar PING_TEMPLATE"),
    ("setvar", "Set a runtime config var.", ".setvar PING_TEMPLATE ✨ Pong!"),
    ("delvar", "Delete a runtime config var.", ".delvar PING_TEMPLATE"),
    ("listvar", "List all runtime config vars.", ".listvar"),
    ("prefix", "Show current command prefixes.", ".prefix"),
]:
    help_menu.add(
        command=cmd,
        description=desc,
        example=ex,
        category="core",
        plugin="config",
    ).register()

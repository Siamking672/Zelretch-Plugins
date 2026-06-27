"""Shell builtin — run a shell command (owner only)."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config
from astralbot.helpers.runner import run_shell
from astralbot.helpers.formatting import code_block

__plugin_name__ = "Shell"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Run a shell command (owner only)."
__plugin_category__ = "core"


@on_command(["sh", "shell"], description="Run a shell command.", permission="owner")
async def sh_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}sh <command>`")

    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text("No command provided.")
    cmd = parts[1]

    msg = await message.edit_text(f"⏳ Running `{cmd}`...")
    output = await run_shell(cmd, timeout=60)
    if len(output) > 3500:
        from astralbot.helpers.paste import paste
        url = await paste(output)
        await msg.edit_text(f"✅ Done.\nOutput: {url}")
    else:
        await msg.edit_text(f"✅ Done.\n{code_block(output, 'bash')}")


help_menu.add(
    command="sh",
    description="Run a shell command (owner only).",
    example=".sh uname -a",
    category="core",
    plugin="sh",
    aliases=["shell"],
).register()

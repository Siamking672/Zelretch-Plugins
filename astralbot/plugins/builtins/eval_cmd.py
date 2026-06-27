"""Eval builtin — execute Python code (owner only)."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config
from astralbot.helpers.runner import run_python
from astralbot.helpers.formatting import code_block

__plugin_name__ = "Eval"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Execute Python code (owner only)."
__plugin_category__ = "core"


@on_command(["eval", "e"], description="Execute Python code.", permission="owner")
async def eval_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}eval <python code>`")

    # message.command[0] is the command name; the rest is the code.
    # We need to grab the raw text after the command — use message.text.
    raw = message.text or message.caption or ""
    # Strip prefix + command
    prefix = Config.primary_prefix
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text("No code provided.")
    code = parts[1]
    # Strip markdown code fences if user wrapped the code
    if code.startswith("```"):
        lines = code.split("\n")
        # Drop first line (```python) and last (```)
        code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    msg = await message.edit_text("⏳ Executing...")
    output = await run_python(code, timeout=30)
    if len(output) > 3500:
        from astralbot.helpers.paste import paste
        url = await paste(output)
        await msg.edit_text(f"✅ Done.\nOutput: {url}")
    else:
        await msg.edit_text(f"✅ Done.\n{code_block(output, 'python')}")


help_menu.add(
    command="eval",
    description="Execute Python code (owner only).",
    example=".eval print('hello')",
    category="core",
    plugin="eval",
    aliases=["e"],
).register()

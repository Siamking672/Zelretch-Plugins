# Zelretch Addons — Figlet ASCII art
# Ported from UltroidAddons/figlet.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}figlet <text>`
    Convert text to ASCII art (figlet).

• `{i}figletlist`
    List available figlet fonts.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"figlet ?(.*)")
async def figlet(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    text = parts[1].strip()
    try:
        import pyfiglet
        art = pyfiglet.figlet_format(text[:30])
        if len(art) > 3500:
            art = art[:3500] + "…"
        await eor(message, f"```\n{art}\n```")
    except ImportError:
        await eor(message, "`pyfiglet not installed. Run: pip install pyfiglet`")
    except Exception as err:
        await eor(message, f"`{err}`")


@zelretch_cmd(pattern="figletlist$")
async def figlet_list(client, message):
    try:
        import pyfiglet
        fonts = pyfiglet.FigletFont.getFonts()
        text = ", ".join(fonts[:100])
        await eor(message, f"`Available fonts ({len(fonts)} total):`\n\n{text}")
    except ImportError:
        await eor(message, "`pyfiglet not installed.`")

# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}figlet <text>`
    Render text as ASCII art (uses pyfiglet if installed).
"""

from __future__ import annotations

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"figlet\s+(.+)")
async def figlet(event):
    text = event.matches[0].group(1)
    try:
        import pyfiglet  # type: ignore
    except ImportError:
        return await eod(event, "Install `pyfiglet` to use this command.", time=10)
    art = pyfiglet.figlet_format(text)
    await eor(event, f"```\n{art}\n```")

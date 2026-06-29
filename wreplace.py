# Zelretch Addons — Word replace
# Ported from UltroidAddons/wreplace.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}wreplace <old> <new> <text>`
    Replace `old` with `new` in `text`.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"wreplace (\S+) (\S+) (.+)")
async def wreplace(client, message):
    try:
        old = message.matches[0].group(1)
        new = message.matches[0].group(2)
        text = message.matches[0].group(3)
    except (AttributeError, IndexError):
        return await eor(message, "`Usage: .wreplace <old> <new> <text>`")
    result = text.replace(old, new)
    await eor(message, f"`{result}`")

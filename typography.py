# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}typography <text>`
    Render text in a few decorative unicode styles.
"""

from __future__ import annotations

from plugins import eor, zelretch_cmd

_STYLES = {
    "bold": lambda s: "".join(_translate(c, 0x1D400, 0x1D41A, 0x1D5D4) for c in s),
    "italic": lambda s: "".join(_translate(c, 0x1D434, 0x1D44E, 0x1D608) for c in s),
    "script": lambda s: "".join(_translate(c, 0x1D49C, 0x1D4B6, 0x1D56C) for c in s),
    "double": lambda s: "".join(_translate(c, 0x1D538, 0x1D552, 0x1D5A0) for c in s),
}

import unicodedata


def _translate(c: str, upper_start: int, lower_start: int, digit_start: int) -> str:
    if "A" <= c <= "Z":
        return chr(upper_start + (ord(c) - ord("A")))
    if "a" <= c <= "z":
        return chr(lower_start + (ord(c) - ord("a")))
    if "0" <= c <= "9":
        return chr(digit_start + (ord(c) - ord("0")))
    return c


@zelretch_cmd(pattern=r"typography\s+(\S+)\s+(.+)")
async def typography(event):
    style = event.matches[0].group(1).lower()
    text = event.matches[0].group(2)
    fn = _STYLES.get(style)
    if not fn:
        return await event.reply(f"Unknown style. Available: {', '.join(_STYLES)}")
    await eor(event, fn(text))

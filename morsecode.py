# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}morse <text>`
    Encode text to Morse code.

• `{i}demorse <code>`
    Decode Morse code to text.
"""

from __future__ import annotations

from plugins import eod, eor, zelretch_cmd

_MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..", "0": "-----", "1": ".----", "2": "..---",
    "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...",
    "8": "---..", "9": "----.", ".": ".-.-.-", ",": "--..--", "?": "..--..",
    "!": "-.-.--", " ": "/",
}
_REVERSE = {v: k for k, v in _MORSE.items()}


@zelretch_cmd(pattern=r"morse\s+(.+)")
async def morse(event):
    text = event.matches[0].group(1).upper()
    parts = [_MORSE.get(c, "?") for c in text]
    await eor(event, "  ".join(parts))


@zelretch_cmd(pattern=r"demorse\s+(.+)")
async def demorse(event):
    code = event.matches[0].group(1).strip().split()
    decoded = "".join(_REVERSE.get(c, "?") for c in code)
    await eor(event, decoded)

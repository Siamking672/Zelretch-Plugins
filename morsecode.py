# Zelretch Addons — Morse code encoder/decoder
# Ported from UltroidAddons/morsecode.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}morse <text>`
    Encode text to Morse code.

• `{i}demorse <morse>`
    Decode Morse code to text.
"""

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    " ": "/",
}
REVERSE = {v: k for k, v in MORSE.items()}

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"morse ?(.*)")
async def morse(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text to encode.`")
    text = parts[1].upper()
    out = " ".join(MORSE.get(ch, "?") for ch in text if ch in MORSE)
    await eor(message, f"`{out}`")


@zelretch_cmd(pattern=r"demorse ?(.*)")
async def demorse(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give Morse code (space-separated).`")
    tokens = parts[1].strip().split()
    out = "".join(REVERSE.get(tok, "?") for tok in tokens)
    await eor(message, f"`{out}`")

# Zelretch Addons — N-Code (number codes)
# Ported from UltroidAddons/ncode.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}ncode <text>`
    Encode text to numeric code (A=01, B=02, ...).

• `{i}ndecode <numbers>`
    Decode numeric code back to text.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"ncode ?(.*)")
async def ncode(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    text = parts[1].upper()
    out = " ".join(f"{ord(ch) - 64:02d}" if ch.isalpha() else str(ord(ch)) for ch in text)
    await eor(message, f"`{out}`")


@zelretch_cmd(pattern=r"ndecode ?(.*)")
async def ndecode(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give numeric code.`")
    tokens = parts[1].split()
    out = []
    for tok in tokens:
        try:
            n = int(tok)
            out.append(chr(n + 64) if 1 <= n <= 26 else chr(n))
        except ValueError:
            out.append("?")
    await eor(message, f"`{''.join(out)}`")

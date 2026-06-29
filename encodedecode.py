# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}encode <text>`
    Base64-encode text.

• `{i}decode <text>`
    Base64-decode text.
"""

from __future__ import annotations

import base64

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"encode\s+(.+)")
async def encode_text(event):
    text = event.matches[0].group(1)
    encoded = base64.b64encode(text.encode()).decode()
    await eor(event, f"**Encoded:**\n`{encoded}`")


@zelretch_cmd(pattern=r"decode\s+(.+)")
async def decode_text(event):
    text = event.matches[0].group(1).strip()
    try:
        decoded = base64.b64decode(text.encode()).decode()
        await eor(event, f"**Decoded:**\n`{decoded}`")
    except Exception as er:
        await eod(event, f"Could not decode: `{er}`", time=5)

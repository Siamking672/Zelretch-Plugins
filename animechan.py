# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}animechan`
    Random anime quote (uses animechan API).
"""

from __future__ import annotations

import json
import urllib.request

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern="animechan$")
async def animechan(event):
    msg = await event.reply("Fetching an anime quote...")
    try:
        req = urllib.request.Request(
            "https://animechan.xyz/api/random",
            headers={"User-Agent": "Zelretch/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        text = (
            f"**{data.get('quote', '')}**\n\n"
            f"— _{data.get('character', '')}_, _{data.get('anime', '')}_"
        )
        await msg.edit(text)
    except Exception as er:
        await eod(msg, f"Could not fetch quote: `{er}`", time=10)

# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}quote`
    Random inspirational quote (via quotefancy / quotable).
"""

from __future__ import annotations

import json
import urllib.request

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern="quote$")
async def quote(event):
    msg = await event.reply("Fetching a quote...")
    try:
        req = urllib.request.Request(
            "https://api.quotable.io/random",
            headers={"User-Agent": "Zelretch/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        text = f"💬 **{data.get('content', '')}**\n\n— _{data.get('author', '')}_"
        await msg.edit(text)
    except Exception as er:
        await eod(msg, f"Could not fetch quote: `{er}`", time=10)

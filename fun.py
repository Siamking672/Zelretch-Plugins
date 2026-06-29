# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}joke`
    Random programming joke.
"""

from __future__ import annotations

import json
import urllib.request

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern="joke$")
async def joke(event):
    msg = await event.reply("Fetching a joke...")
    try:
        req = urllib.request.Request(
            "https://v2.jokeapi.dev/joke/Programming?safe-mode",
            headers={"User-Agent": "Zelretch/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data.get("type") == "single":
            text = data.get("joke", "")
        else:
            text = f"{data.get('setup', '')}\n\n||{data.get('delivery', '')}||"
        await msg.edit(text)
    except Exception as er:
        await eod(msg, f"Could not fetch joke: `{er}`", time=10)

# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}astronomy`
    Fetch the astronomy picture of the day (NASA APOD).
    Set ``NASA_API_KEY`` via `.setvar` to use a personal key (otherwise DEMO_KEY).
"""

from __future__ import annotations

import json
import urllib.request

from plugins import eod, eor, udB, zelretch_cmd


@zelretch_cmd(pattern="astronomy$")
async def astronomy(event):
    api_key = (udB.get_key("NASA_API_KEY") if udB else None) or "DEMO_KEY"
    msg = await event.reply("Fetching astronomy picture of the day...")
    try:
        url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "Zelretch/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        text = (
            f"**{data.get('title', 'Astronomy Picture of the Day')}**\n\n"
            f"{data.get('explanation', '')}\n\n"
            f"[Image URL]({data.get('url')})"
        )
        await msg.edit(text, disable_web_page_preview=False)
    except Exception as er:
        await eod(msg, f"Could not fetch APOD: `{er}`", time=10)

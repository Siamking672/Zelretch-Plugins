# Zelretch Addons — Astronomy picture of the day
# Ported from UltroidAddons/astronomy.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}apod`
    Fetch NASA's Astronomy Picture of the Day.
"""

import requests

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="apod$")
async def apod(client, message):
    msg = await message.reply_text("`Fetching APOD…`")
    try:
        resp = requests.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", timeout=15)
        data = resp.json()
        title = data.get("title", "Astronomy Picture of the Day")
        explanation = data.get("explanation", "")[:600]
        url = data.get("hdurl") or data.get("url")
        if url:
            await client.send_photo(message.chat.id, url, caption=f"**{title}**\n\n{explanation}")
            await msg.delete()
        else:
            await msg.edit_text(f"**{title}**\n\n{explanation}")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

# Zelretch Addons — Waifu image generator
# Ported from UltroidAddons/waifu.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}waifu`
    Get a random waifu image.
"""

import requests

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="waifu$")
async def waifu(client, message):
    msg = await message.reply_text("`Fetching waifu…`")
    try:
        resp = requests.get("https://api.waifu.pics/sfw/waifu", timeout=15)
        data = resp.json()
        url = data.get("url")
        if url:
            await client.send_photo(message.chat.id, url)
            await msg.delete()
        else:
            await msg.edit_text("`Could not fetch image.`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

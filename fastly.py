# Zelretch Addons — Fast.ly URL shortener
# Ported from UltroidAddons/fastly.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}shorten <url>`
    Shorten a URL using is.gd.
"""

import requests

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"shorten ?(.*)")
async def shorten(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give a URL.`")
    url = parts[1].strip()
    msg = await message.reply_text("`Shortening…`")
    try:
        resp = requests.get(
            "https://is.gd/create.php",
            params={"format": "simple", "url": url},
            timeout=15,
        )
        if resp.status_code == 200 and resp.text.startswith("http"):
            await msg.edit_text(f"**Shortened:** {resp.text}")
        else:
            await msg.edit_text(f"`{resp.text}`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

# Zelretch Addons — Wikipedia-style quote
# Ported from UltroidAddons/quotefancy.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}quotefancy <text>`
    Generate a fancy quote image.
"""

import io
import requests

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"quotefancy ?(.*)")
async def quotefancy(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    text = parts[1].strip()
    msg = await message.reply_text("`Generating fancy quote…`")
    try:
        resp = requests.get(
            "https://api.quotable.io/random",
            timeout=10,
        )
        # Build a simple text-image using quotefancy APIs (or fall back).
        # Use a public placeholder service.
        img_resp = requests.get(
            "https://dummyimage.com/600x200/7c5cff/ffffff.png&text=" + text[:80],
            timeout=15,
        )
        if img_resp.status_code == 200:
            buf = io.BytesIO(img_resp.content)
            buf.name = "quote.png"
            await client.send_photo(message.chat.id, buf, caption=f"_{text}_")
            await msg.delete()
        else:
            await msg.edit_text("`Could not generate image.`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

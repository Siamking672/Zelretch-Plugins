# Zelretch Addons — QR code generator
# Ported from Ultroid plugins/qrcode.py
# Copyright (C) 2021-2026 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}qr <text>`
    Generate a QR code from text.
"""

import io

import requests

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"qr ?(.*)")
async def qr(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return await eor(message, "`Give some text to encode.`")
    text = parts[1].strip()
    msg = await message.reply_text("`Generating QR code…`")
    try:
        resp = requests.get(
            "https://api.qrserver.com/v1/create-qr-code/",
            params={"size": "500x500", "data": text},
            timeout=15,
        )
        if resp.status_code == 200:
            buf = io.BytesIO(resp.content)
            buf.name = "qr.png"
            await client.send_photo(message.chat.id, buf, caption=f"**QR code for:** `{text[:80]}`")
            await msg.delete()
        else:
            await msg.edit_text("`QR generation failed.`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

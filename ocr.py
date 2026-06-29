# Zelretch Addons — OCR (image to text)
# Ported from UltroidAddons/ocr.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}ocr <reply to image>`
    Extract text from an image (uses OCR.space free API).
"""

import requests

from zelretch.config import get_config
from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="ocr$")
async def ocr(client, message):
    reply = message.reply_to_message
    if not reply or not reply.photo:
        return await eor(message, "`Reply to an image to extract text.`")
    msg = await message.reply_text("`Extracting text…`")
    try:
        photo = await reply.download(in_memory=True)
        api_key = get_config("OCR_SPACE_API_KEY", "helloworld")
        resp = requests.post(
            "https://api.ocr.space/parse/image",
            files={"filename": ("img.jpg", photo.read(), "image/jpeg")},
            data={"apikey": api_key, "language": "eng"},
            timeout=30,
        )
        data = resp.json()
        parsed = data.get("ParsedResults", [{}])[0].get("ParsedText", "").strip()
        if parsed:
            await msg.edit_text(f"**Extracted text:**\n\n`{parsed[:3000]}`")
        else:
            await msg.edit_text("`No text recognized.`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

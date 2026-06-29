# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}ocr`
    Run OCR on the replied image (uses ``pytesseract`` if installed).
"""

from __future__ import annotations

import os
import tempfile

from plugins import eod, eor, zelretch_bot, zelretch_cmd


@zelretch_cmd(pattern="ocr$")
async def ocr(event):
    if not event.reply_to_message or not event.reply_to_message.photo:
        return await eod(event, "Reply to an image.", time=5)
    if zelretch_bot is None:
        return
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        return await eod(event, "Install `pytesseract` and `Pillow` (plus the tesseract binary).", time=10)
    msg = await event.reply("Running OCR...")
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        path = f.name
    try:
        await zelretch_bot.download_media(event.reply_to_message, file_name=path)
        text = pytesseract.image_to_string(Image.open(path))
        await msg.edit(f"**OCR result:**\n\n`{text.strip() or '(no text detected)'}`")
    except Exception as er:
        await eod(msg, f"OCR failed: `{er}`", time=10)
    finally:
        os.unlink(path)

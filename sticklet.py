# Zelretch Addons — Sticklet (text sticker)
# Ported from UltroidAddons/sticklet.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}sticklet <text>`
    Convert text to a sticker-style image (PNG).
"""

import io

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"sticklet ?(.*)")
async def sticklet(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    text = parts[1].strip()
    msg = await message.reply_text("`Generating sticklet…`")
    try:
        from PIL import Image, ImageDraw, ImageFont
        # Render text to a small PNG (best-effort).
        img = Image.new("RGB", (512, 128), color=(36, 38, 50))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except Exception:
            font = ImageFont.load_default()
        # Center the text.
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            w, h = 200, 40
        x = max(10, (512 - w) // 2)
        y = max(10, (128 - h) // 2)
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "sticklet.png"
        await client.send_document(message.chat.id, buf, force_document=False)
        await msg.delete()
    except ImportError:
        await msg.edit_text("`pillow not installed. Run: pip install pillow`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

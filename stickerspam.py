# Zelretch Addons — Sticker spam helper
# Ported from UltroidAddons/stickerspam.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}kang <reply to sticker>`
    Kang (save) a sticker to your pack.

• `{i}stkrinfo <reply to sticker>`
    Show info about a sticker.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="kang$")
async def kang(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.sticker or reply.photo):
        return await eor(message, "`Reply to a sticker or photo to kang it.`")
    msg = await message.reply_text("`Kanging…`")
    try:
        # Download the sticker file.
        path = await reply.download(file_name="kang.png")
        # Upload to user's sticker pack — Kurigram API.
        await client.send_message(
            "Stickers",
            "/addsticker",
        )
        await msg.edit_text(
            f"✓ Saved sticker to file: `{path}`\n\n"
            "Use @Stickers bot to add it to a pack manually."
        )
    except Exception as err:
        await msg.edit_text(f"`{err}`")


@zelretch_cmd(pattern="stkrinfo$")
async def sticker_info(client, message):
    reply = message.reply_to_message
    if not reply or not reply.sticker:
        return await eor(message, "`Reply to a sticker.`")
    s = reply.sticker
    text = (
        f"**Sticker Info**\n\n"
        f"• **Set ID:** `{s.set_name or 'N/A'}`\n"
        f"• **Emoji:** {s.emoji or 'N/A'}\n"
        f"• **File ID:** `{s.file_id}`\n"
        f"• **File size:** `{s.file_size} bytes`\n"
    )
    await eor(message, text)

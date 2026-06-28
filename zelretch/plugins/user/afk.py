import os
import random
import time

from kurigram import Client, filters
from kurigram.enums import MessageMediaType
from kurigram.types import Message

from zelretch.core import Config, db, zelretch
from zelretch.functions.formatter import add_to_dict, get_from_dict, readable_time
from zelretch.functions.images import convert_to_png

from . import HelpMenu, custom_handler, group_only, on_message

afk_quotes = [
    "🚶‍♂️ Taking a break, be back soon!",
    "⏳ AFK - Away From the Keyboard momentarily.",
    "🔜 Stepped away, but I'll return shortly.",
    "👋 Gone for a moment, not forgotten.",
    "🌿 Taking a breather, back in a bit.",
    "📵 Away for a while, feel free to leave a message!",
    "⏰ On a short break, back shortly.",
    "🌈 Away from the screen, catching a breath.",
    "💤 Offline for a moment, but still here in spirit.",
    "🚀 Exploring the real world, back in a moment!",
    "🍵 Taking a tea break, back shortly!",
    "🌙 Resting my keyboard, back after a short nap.",
    "🚶‍♀️ Stepping away for a moment of peace.",
    "🎵 AFK but humming along, back shortly!",
    "🌞 Taking a sunshine break, back soon!",
    "🌊 Away, catching some waves of relaxation.",
    "🚪 Temporarily closed, be back in a bit!",
    "🌸 Taking a moment to smell the digital roses.",
    "🍃 Stepped into the real world for a while.",
]


@on_message("afk")
async def afk(_, message: Message):
    if not message.from_user:
        return
    if await db.is_afk(message.from_user.id):
        return await zelretch.delete(message, "🙄 𝖨'𝗆 𝖺𝗅𝗋𝖾𝖺𝖽𝗒 𝖠𝖥𝖪!")

    media_type = None
    media = None

    if message.reply_to_message and message.reply_to_message.media:
        if message.reply_to_message.media == MessageMediaType.ANIMATION:
            media_type = "animation"
        elif message.reply_to_message.media == MessageMediaType.AUDIO:
            media_type = "audio"
        elif message.reply_to_message.media == MessageMediaType.PHOTO:
            media_type = "photo"
        elif message.reply_to_message.media == MessageMediaType.STICKER:
            media_type = "sticker"
        elif message.reply_to_message.media == MessageMediaType.VIDEO:
            media_type = "video"
        elif message.reply_to_message.media == MessageMediaType.VOICE:
            media_type = "voice"

        media = await message.reply_to_message.forward(Config.LOGGER_ID)

    reason = await zelretch.input(message)
    reason = reason if reason else "Not specified"

    await db.set_afk(
        message.from_user.id, reason, media.id if media else None, media_type
    )
    await zelretch.delete(message, "🫡 𝖦𝗈𝗂𝗇𝗀 𝖠𝖥𝖪! 𝖲𝖾𝖾 𝗒𝖺'𝗅𝗅 𝗅𝖺𝗍𝖾𝗋.")
    await zelretch.check_and_log(
        "afk",
        f"Going AFK! \n\n**Reason:** `{reason}`",
    )
    add_to_dict(Config.AFK_CACHE, [message.from_user.id, message.chat.id])


@custom_handler(filters.incoming & ~filters.bot & ~filters.service)
async def afk_watch(client: Client, message: Message):
    if not message.from_user:
        return

    afk_data = await db.get_afk(client.me.id)
    if not afk_data:
        return

    if message.from_user.id == afk_data["user_id"]:
        return

    if message.chat.type in group_only:
        if not message.mentioned:
            return

    afk_time = readable_time(round(time.time() - afk_data["time"]))
    caption = f"**{random.choice(afk_quotes)}**\n\n**💫 𝖱𝖾𝖺𝗌𝗈𝗇:** {afk_data['reason']}\n**⏰ 𝖠𝖥𝖪 𝖥𝗋𝗈𝗆:** `{afk_time}`"

    if afk_data["media_type"] == "animation":
        media = await client.get_messages(Config.LOGGER_ID, afk_data["media"])
        sent = await client.send_animation(
            message.chat.id,
            media.animation.file_id,
            caption=caption,
            reply_to_message_id=message.id,
        )

    elif afk_data["media_type"] in ["audio", "photo", "video", "voice"]:
        sent = await client.copy_message(
            message.chat.id,
            Config.LOGGER_ID,
            afk_data["media"],
            caption,
            reply_to_message_id=message.id,
        )

    elif afk_data["media_type"] == "sticker":
        media = await client.get_messages(Config.LOGGER_ID, afk_data["media"])
        sticker_path = await client.download_media(media, file_name=Config.TEMP_DIR + "sticker.png")
        try:
            converted = convert_to_png(sticker_path)
        except Exception:
            converted = sticker_path
        sent = await message.reply_photo(converted, caption=caption)
        media = converted

    else:
        sent = await message.reply_text(caption)

    link = message.link if message.chat.type in group_only else "No DM Link"

    await zelretch.check_and_log(
        "afk",
        f"{message.from_user.mention} mentioned you when you were AFK! \n\n**Link:** {link}",
    )
    try:
        data = get_from_dict(Config.AFK_CACHE, [afk_data["user_id"], message.chat.id])
        if data:
            await client.delete_messages(message.chat.id, data)
        add_to_dict(Config.AFK_CACHE, [afk_data["user_id"], message.chat.id], sent.id)
    except KeyError:
        add_to_dict(Config.AFK_CACHE, [afk_data["user_id"], message.chat.id], sent.id)


@custom_handler(filters.outgoing, 2)
async def remove_afk(_, message: Message):
    if not message.from_user:
        return
    if await db.is_afk(message.from_user.id):
        if message.text and "afk" in message.text:
            return

        data = await db.get_afk(message.from_user.id)
        total_afk_time = readable_time(round(time.time() - data["time"]))

        kaleido = await message.reply_text(
            f"🫡 **𝖡𝖺𝖼𝗄 𝗍𝗈 𝗏𝗂𝗋𝗍𝗎𝖺𝗅 𝗐𝗈𝗋𝗅𝖽! \n\n⌚ Was away for:** `{total_afk_time}`"
        )
        await message.delete()

        await db.rm_afk(message.from_user.id)
        await zelretch.check_and_log(
            "afk",
            f"Returned from AFK! \n\n**Time:** `{total_afk_time}`\n**Link:** {kaleido.link}",
        )


HelpMenu("afk").add(
    "afk",
    "<reason (optional)>",
    "Mark yourself as Away From Keyboard. Anyone who mentions you will receive an automatic reply with your reason and the time elapsed. Reply to a media message to attach it to the AFK notice.",
    "afk catching some sleep",
    "Sending any message in any chat automatically clears the AFK status. Include the word 'afk' in your message to stay AFK while sending it.",
).info("Away From Keyboard — let the bot answer mentions for you while you are away.").done()

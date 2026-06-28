import asyncio
import re

from kurigram import Client, filters
from kurigram.enums import MessageMediaType
from kurigram.types import Message

from . import HelpMenu, custom_handler, db, handler, zelretch, on_message, Config


@on_message("filter", allow_master=True)
async def set_filter(client: Client, message: Message):
    if len(message.command) < 2 or not message.reply_to_message:
        return await zelretch.delete(
            message, f"Reply to a message with {handler}filter <keyword> to save it as a filter."
        )

    keyword = await zelretch.input(message)
    kaleido = await zelretch.edit(message, f"Saving filter `{keyword}`")
    msg = await message.reply_to_message.forward(Config.LOGGER_ID)

    await db.set_filter(client.me.id, message.chat.id, keyword.lower(), msg.id)
    await zelretch.delete(kaleido, f"**🍀 𝖭𝖾𝗐 𝖥𝗂𝗅𝗍𝖾𝗋 𝖲𝖺𝗏𝖾𝖽:** `{keyword}`")
    await msg.reply_text(
        f"**🍀 𝖭𝖾𝗐 𝖥𝗂𝗅𝗍𝖾𝗋 𝖲𝖺𝗏𝖾𝖽:** `{keyword}`\n\n**DO NOT DELETE THIS MESSAGE!!!**",
    )


@on_message(["rmfilter", "rmallfilter"], allow_master=True)
async def rmfilter(client: Client, message: Message):
    if len(message.command[0]) < 9:
        if len(message.command) < 2:
            return await zelretch.delete(message, "Give a filter name to remove.")

        keyword = await zelretch.input(message)
        kaleido = await zelretch.edit(message, f"Removing filter `{keyword}`")

        if await db.is_filter(client.me.id, message.chat.id, keyword.lower()):
            await db.rm_filter(client.me.id, message.chat.id, keyword.lower())
            await zelretch.delete(kaleido, f"**🍀 𝖥𝗂𝗅𝗍𝖾𝗋 𝖱𝖾𝗆𝗈𝗏𝖾𝖽:** `{keyword}`")
        else:
            await zelretch.delete(kaleido, f"**🍀 𝖥𝗂𝗅𝗍𝖾𝗋 𝖽𝗈𝖾𝗌 𝗇𝗈𝗍 𝖾𝗑𝗂𝗌𝗍𝗌:** `{keyword}`")
    else:
        kaleido = await zelretch.edit(message, "Removing all filters...")

        await db.rm_all_filters(client.me.id, message.chat.id)
        await zelretch.delete(kaleido, "All filters have been removed.")


@on_message(["getfilter", "getfilters"], allow_master=True)
async def allfilters(client: Client, message: Message):
    if len(message.command) > 1:
        keyword = await zelretch.input(message)
        kaleido = await zelretch.edit(message, f"Getting filter `{keyword}`")

        if await db.is_filter(client.me.id, message.chat.id, keyword.lower()):
            data = await db.get_filter(client.me.id, message.chat.id, keyword.lower())
            msgid = None
            for f in data["filter"]:
                if f["keyword"] == keyword.lower():
                    msgid = f["msgid"]
                    break
            if msgid is None:
                return await zelretch.delete(kaleido, "Filter does not exist.")
            sent = await client.copy_message(message.chat.id, Config.LOGGER_ID, msgid)

            await sent.reply_text(f"**🍀 𝖥𝗂𝗅𝗍𝖾𝗋:** `{keyword}`")
            await kaleido.delete()

        else:
            await zelretch.delete(kaleido, f"**🍀 𝖥𝗂𝗅𝗍𝖾𝗋 𝖽𝗈𝖾𝗌 𝗇𝗈𝗍 𝖾𝗑𝗂𝗌𝗍𝗌:** `{keyword}`")

    else:
        kaleido = await zelretch.edit(message, "Getting all filters...")
        filters = await db.get_all_filters(client.me.id, message.chat.id)

        if filters:
            text = f"**🍀 𝖭𝗈. 𝗈𝖿 𝖥𝗂𝗅𝗍𝖾𝗋𝗌 𝗂𝗇 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍:** `{len(filters)}`\n\n"

            for i, filter in enumerate(filters, 1):
                text += f"** {'0' if i < 10 else ''}{i}:** `{filter['keyword']}`\n"

            await kaleido.edit(text)

        else:
            await zelretch.delete(kaleido, "No filters in this chat.")


@custom_handler(filters.incoming & ~filters.service)
async def handle_filters(client: Client, message: Message):
    data = await db.get_all_filters(client.me.id, message.chat.id)
    if not data:
        return

    msg = message.text or message.caption
    if not msg:
        return

    for filter in data:
        pattern = r"( |^|[^\w])" + re.escape(filter["keyword"]) + r"( |$|[^\w])"
        if re.search(pattern, msg, flags=re.IGNORECASE):
            msgid = filter["msgid"]
            await client.copy_message(message.chat.id, Config.LOGGER_ID, msgid, reply_to_message_id=message.id)
            await asyncio.sleep(1)


HelpMenu("filters").add(
    "filter",
    "<keyword> <reply to a message>",
    "Bind a keyword to the replied message. Whenever anyone sends the keyword in this chat, the userbot replies with the saved message.",
    "filter rules",
    "Reply to the message you want to save. Text, photos, videos, stickers, and documents with captions are all supported.",
).add(
    "rmfilter",
    "<keyword>",
    "Remove a single filter by its keyword.",
    "rmfilter rules",
).add(
    "rmallfilter",
    None,
    "Delete every filter configured in the current chat in one go.",
    "rmallfilter",
).add(
    "getfilter",
    "<keyword>",
    "Preview the saved message for a specific filter keyword.",
    "getfilter rules",
).add(
    "getfilters",
    None,
    "List every filter keyword currently active in the chat.",
    "getfilters",
).info(
    "Auto-reply filters — when a keyword is mentioned, the bot replies with the saved message."
).done()

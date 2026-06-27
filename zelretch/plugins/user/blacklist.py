import re

from pyrogram import Client, filters
from pyrogram.types import Message

from zelretch.core import Config, Symbols
from zelretch.functions.utility import BList

from . import HelpMenu, custom_handler, db, zelretch, on_message


@on_message("blacklist", admin_only=True, allow_master=True)
async def blacklist(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me something to blacklist.")

    text = await zelretch.input(message)

    if await db.is_blacklist(client.me.id, message.chat.id, text):
        return await zelretch.delete(message, f"**Already blacklisted** `{text}`")

    await BList.addBlacklist(client.me.id, message.chat.id, text)
    await zelretch.delete(message, f"**Blacklisted:** `{text}`")


@on_message("unblacklist", admin_only=True, allow_master=True)
async def unblacklist(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me something to unblacklist.")

    text = await zelretch.input(message)

    if not await db.is_blacklist(client.me.id, message.chat.id, text):
        return await zelretch.delete(message, f"`{text}` does not exist in blacklist.")

    await BList.rmBlacklist(client.me.id, message.chat.id, text)
    await zelretch.delete(message, f"**Unblacklisted:** `{text}`")


@on_message("blacklists", admin_only=True, allow_master=True)
async def blacklists(client: Client, message: Message):
    blacklists = await db.get_all_blacklists(client.me.id, message.chat.id)

    if not blacklists:
        return await zelretch.delete(message, "No blacklists found.")

    text = f"**{Symbols.bullet} 𝖡𝗅𝖺𝖼𝗄𝗅𝗂𝗌𝗍𝗌 𝗂𝗇 {message.chat.title}:**\n\n"
    for i in blacklists:
        text += f"    {Symbols.anchor} `{i}`\n"

    await zelretch.edit(message, text)


@custom_handler(filters.text & filters.incoming & ~Config.AUTH_USERS & ~filters.service)
async def handle_blacklists(client: Client, message: Message):
    if BList.check_client_chat(client.me.id, message.chat.id):
        blacklists = BList.getBlacklists(client.me.id, message.chat.id)
        for blacklist in blacklists:
            pattern = r"( |^|[^\w])" + re.escape(blacklist) + r"( |$|[^\w])"
            if re.search(pattern, message.text, flags=re.IGNORECASE):
                try:
                    await message.delete()
                except Exception:
                    await BList.rmBlacklist(client.me.id, message.chat.id, blacklist)


HelpMenu("blacklist").add(
    "blacklist",
    "<text>",
    "Add the text to blacklist. If the text is sent in the chat it will be deleted.",
    "blacklist hello",
).add(
    "unblacklist", "<text>", "Remove the text from blacklist.", "unblacklist hello"
).add(
    "blacklists", None, "List all the blacklisted words in the chat.", "blacklists"
).info(
    "Blacklist Module"
).done()

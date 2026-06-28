from kurigram import Client, filters
from kurigram.types import Message

from zelretch.core import Symbols

from . import HelpMenu, custom_handler, db, group_n_channel, zelretch, on_message


@on_message("autopost", chat_type=group_n_channel, allow_master=True)
async def autopost(client: Client, message: Message):
    if len(message.command) != 2:
        return await zelretch.delete(
            message, "Wrong usage of command.\nCheck help menu for more info."
        )

    kaleido = await zelretch.edit(message, "Starting Autopost in this group/channel...")

    post_from = message.command[1]
    _chat = await client.get_chat(post_from)

    if not _chat:
        return await zelretch.delete(kaleido, "Invalid chat/channel id.")

    if _chat.type not in group_n_channel:
        return await zelretch.delete(
            kaleido, "You can only autopost in groups and channels."
        )

    if _chat.id == message.chat.id:
        return await zelretch.delete(
            kaleido, "You can't autopost in the same group/channel."
        )

    if await db.is_autopost(client.me.id, _chat.id, message.chat.id):
        return await zelretch.delete(
            kaleido, "This group/channel is already in autopost list."
        )

    await db.set_autopost(client.me.id, _chat.id, message.chat.id)

    await zelretch.delete(
        kaleido, f"Autopost started from {_chat.title} to {message.chat.title}."
    )
    await zelretch.check_and_log(
        "autopost start",
        f"**AutoPost From:** {_chat.title} \n**AutoPost To:** {message.chat.title}\n**AutoPost By:** {client.me.mention}",
    )


@on_message("stopautopost", chat_type=group_n_channel, allow_master=True)
async def stop_autopost(client: Client, message: Message):
    if len(message.command) != 2:
        return await zelretch.delete(
            message, "Wrong usage of command.\nCheck help menu for more info."
        )

    kaleido = await zelretch.edit(message, "Stopping Autopost in this group/channel...")

    post_from = message.command[1]
    _chat = await client.get_chat(post_from)

    if not _chat:
        return await zelretch.delete(kaleido, "Invalid chat/channel id.")

    if _chat.type not in group_n_channel:
        return await zelretch.delete(
            kaleido, "You can only autopost in groups and channels."
        )

    if not await db.is_autopost(client.me.id, _chat.id, message.chat.id):
        return await zelretch.delete(kaleido, "This group/channel is not in autopost list.")

    await db.rm_autopost(client.me.id, _chat.id, message.chat.id)

    await zelretch.delete(
        kaleido, f"Autopost stopped from {_chat.title} to {message.chat.title}."
    )
    await zelretch.check_and_log(
        "autopost stop",
        f"**AutoPost From:** {_chat.title} \n**AutoPost To:** {message.chat.title}\n**AutoPost By:** {client.me.mention}",
    )


@on_message("autoposts", chat_type=group_n_channel, allow_master=True)
async def autoposts(client: Client, message: Message):
    kaleido = await zelretch.edit(message, "Getting autopost list...")

    data = await db.get_all_autoposts(client.me.id)
    if not data:
        return await zelretch.delete(kaleido, "No autoposts found.")

    text = f"**𝖠𝖼𝗍𝗂𝗏𝖾 𝖠𝗎𝗍𝗈𝗉𝗈𝗌𝗍𝗌 𝖿𝗈𝗋: {client.me.mention}**\n\n"
    for doc in data:
        for entry in doc.get("autopost", []):
            from_chat = await client.get_chat(entry["from_channel"])
            to_chat = await client.get_chat(entry["to_channel"])

            from_chat_name = (
                f"{from_chat.title} [{from_chat.id}]" if from_chat else entry["from_channel"]
            )
            to_chat_name = f"{to_chat.title} [{to_chat.id}]" if to_chat else entry["to_channel"]

            text += f"   {Symbols.anchor} **From:** {from_chat_name}\n"
            text += f"   {Symbols.anchor} **To:** {to_chat_name}\n"
            text += f"   {Symbols.anchor} **Date:** {entry['date']}\n\n"

    await zelretch.edit(kaleido, text)


@custom_handler(filters.incoming & (filters.group | filters.channel) & ~filters.service)
async def handle_autopost(client: Client, message: Message):
    if not await db.is_autopost(client.me.id, message.chat.id):
        return

    data = await db.get_autopost(client.me.id, message.chat.id)
    if not data:
        return

    for entry in data.get("autopost", []):
        if entry["from_channel"] != message.chat.id:
            continue
        await message.copy(int(entry["to_channel"]))


HelpMenu("autopost").add(
    "autopost",
    "<source channel id/username>",
    "Forward every new post from the source channel into the current chat without a forward tag. The userbot must be a member of the source channel.",
    "autopost @zelretch_news",
    "Posts are copied as new messages, so they appear native to the destination chat.",
).add(
    "stopautopost",
    "<source channel id/username>",
    "Stop forwarding posts from the specified source channel into the current chat.",
    "stopautopost @zelretch_news",
).add(
    "autoposts",
    None,
    "List every active autopost feed configured for the current chat.",
    "autoposts",
).info(
    "Mirror posts from one chat to another without forward tags."
).done()

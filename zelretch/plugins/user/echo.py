from kurigram import Client
from kurigram.types import Message

from zelretch.core import Symbols

from . import HelpMenu, db, zelretch, on_message


@on_message("echo", allow_master=True)
async def echo(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        user = (await client.get_users(message.command[1])).id
    else:
        return await zelretch.delete(
            message, "Reply to an user or pass me a user id to start echoing!"
        )

    if await db.is_echo(client.me.id, message.chat.id, user):
        return await zelretch.delete(message, "Echo is already enabled for this user!")

    await db.set_echo(client.me.id, message.chat.id, user)
    await zelretch.delete(message, "Echo enabled for this user!")


@on_message("unecho", allow_master=True)
async def unecho(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        user = (await client.get_users(message.command[1])).id
    else:
        return await zelretch.delete(
            message, "Reply to an user or pass me a user id to stop echoing!"
        )

    if not await db.is_echo(client.me.id, message.chat.id, user):
        return await zelretch.delete(message, "Echo is already disabled for this user!")

    await db.rm_echo(client.me.id, message.chat.id, user)
    await zelretch.delete(message, "Echo disabled for this user!")


@on_message("listecho", allow_master=True)
async def listecho(client: Client, message: Message):
    echos = await db.get_all_echo(client.me.id, message.chat.id)
    if not echos:
        return await zelretch.delete(message, "No echos in this chat!")

    text = "**𝖫𝗂𝗌𝗍 𝗈𝖿 𝖤𝖼𝗁𝗈 𝗂𝗇 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍:**\n\n"
    for echo in echos:
        text += f"    {Symbols.anchor} `{echo}`\n"

    await zelretch.edit(message, text)


@on_message(["resend", "copy"], allow_master=True)
async def reSend(_, message: Message):
    if message.reply_to_message:
        await message.reply_to_message.copy(
            message.chat.id, reply_to_message_id=message.reply_to_message.id
        )
    await message.delete()


HelpMenu("echo").add(
    "echo",
    "<reply to user> or <user id>",
    "Mirror every text or sticker message the target user sends in this chat. The userbot will repost their message content immediately after they send it.",
    "echo @ZelretchUser",
    "Only text messages and stickers are echoed — media, voice, and animations are ignored.",
).add(
    "unecho",
    "<reply to user> or <user id>",
    "Stop echoing a user's messages in the current chat.",
    "unecho @ZelretchUser",
).add(
    "listecho",
    None,
    "List every user whose messages are currently being echoed in this chat.",
    "listecho",
).add(
    "resend",
    "<reply to message>",
    "Forward the replied message as a new message without a forward tag, preserving its content and media.",
    "resend",
    "Alias 'copy' can also be used.",
).info(
    "Mirror or copy messages — echo users in real time, or resend a single message anonymously."
).done()

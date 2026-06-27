import asyncio

from kurigram import Client
from kurigram.errors.exceptions import FloodWait
from kurigram.types import Message

from . import HelpMenu, zelretch, on_message


def _chunk(from_msg: int, to_msg: int):
    curr_msg = from_msg

    while curr_msg < to_msg:
        yield list(range(curr_msg, min(curr_msg + 100, to_msg)))
        curr_msg += 100


@on_message("purge", allow_master=True)
async def purgeMsg(client: Client, message: Message):
    if not message.reply_to_message:
        return await zelretch.delete(
            message, "__Reply to a message to delete all messages after that.__"
        )

    deleted = 0
    from_msg = message.reply_to_message

    kaleido = await zelretch.edit(message, "__Purging...__")
    for msg_ids in range(from_msg.id, message.id + 1):
        try:
            status = await client.delete_messages(message.chat.id, msg_ids)
            deleted += status
        except FloodWait as e:
            await asyncio.sleep(e.value)
            status = await client.delete_messages(message.chat.id, msg_ids)
            deleted += status
        except:
            pass

    await zelretch.delete(kaleido, f"__🧹 Purged {deleted} messages.__")


@on_message("purgeme", allow_master=True)
async def purgeMe(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(
            message, "__Give the number of messages you want to delete.__"
        )
    try:
        count = int(message.command[1])
    except:
        return await zelretch.delete(message, "Argument must be an integer.")

    kaleido = await zelretch.edit(message, "__Purging...__")
    async for msgs in client.search_messages(
        message.chat.id, limit=count, from_user="me"
    ):
        try:
            await msgs.delete()
        except:
            pass

    await zelretch.delete(kaleido, f"__🧹 Purged {count} messages.__")


@on_message("purgeuser", allow_master=True)
async def purgeUser(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await zelretch.delete(
            message, "__Reply to a user to delete their messages.__"
        )

    count = 0
    if len(message.command) > 1:
        try:
            count = int(message.command[1])
        except:
            return await zelretch.delete(message, "Argument must be an integer.")

    kaleido = await zelretch.edit(message, "__Purging...__")
    async for msgs in client.search_messages(
        message.chat.id, limit=count, from_user=message.reply_to_message.from_user.id
    ):
        try:
            await msgs.delete()
        except:
            pass

    await zelretch.delete(
        kaleido,
        f"__🧹 Purged {count} messages of {message.reply_to_message.from_user.mention}.__,,"
    )


@on_message("del", allow_master=True)
async def delMsg(_, message: Message):
    if not message.reply_to_message:
        return await zelretch.delete(
            message, "__Reply to a message to delete that message.__"
        )

    await message.reply_to_message.delete()
    await message.delete()


@on_message(["selfdestruct", "sd"], allow_master=True)
async def selfdestruct(client: Client, message: Message):
    if len(message.command) < 3:
        return await zelretch.delete(
            message, "__Give the number of seconds and the message to self-destruct.__"
        )

    try:
        seconds = int(message.command[1])
    except:
        return await zelretch.delete(message, "Argument must be an integer.")

    msg = " ".join(message.command[2:])
    await message.delete()
    x = await client.send_message(message.chat.id, msg)
    await asyncio.sleep(seconds)
    await x.delete()


HelpMenu("purge").add(
    "purge",
    "<reply to message>",
    "Delete every message in the current chat starting from the replied message up to the most recent one. The userbot must be an admin with delete-message permission.",
    "purge",
).add(
    "purgeme",
    "<count>",
    "Delete your own last N messages from the current chat.",
    "purgeme 20",
).add(
    "purgeuser",
    "<reply to user> <count>",
    "Delete the last N messages sent by the replied user in the current chat.",
    "purgeuser @ZelretchUser 20",
).add(
    "del",
    "<reply to message>",
    "Delete the single replied message.",
    "del",
).add(
    "selfdestruct",
    "<seconds> <message text>",
    "Send a message that automatically deletes itself after the specified number of seconds.",
    "selfdestruct 10 This message will vanish.",
    "Alias 'sd' can also be used.",
).info(
    "Message deletion tools — purge ranges, delete singles, clean up your own messages, or send self-destructing notes."
).done()

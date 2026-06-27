import asyncio

from kurigram import Client
from kurigram.types import Message

from . import HelpMenu, Symbols, zelretch, on_message

spamTask = {}


async def spam_text(
    client: Client,
    chat_id: int,
    to_spam: str,
    count: int,
    reply_to: int,
    delay: float,
    copy_id: int,
    event: asyncio.Event,
):
    for _ in range(count):
        if event.is_set():
            break

        if copy_id:
            await client.copy_message(
                chat_id, chat_id, copy_id, reply_to_message_id=reply_to
            )
        else:
            await client.send_message(
                chat_id,
                to_spam,
                disable_web_page_preview=True,
                reply_to_message_id=reply_to,
            )
        if delay:
            await asyncio.sleep(delay)

    try:
        event.set()
        task = spamTask.get(chat_id, None)
        if task:
            task.remove(event)
    except:
        pass

    await zelretch.check_and_log(
        "spam",
        f"**Count:** `{count}`\n**Chat:** `{chat_id}`\n**Client:** {client.me.first_name}",
    )


@on_message("spam", allow_master=True)
async def spamMessage(client: Client, message: Message):
    if len(message.command) < 3:
        return await zelretch.delete(message, "Give me something to spam.")

    reply_to = message.reply_to_message.id if message.reply_to_message else None
    try:
        count = int(message.command[1])
    except ValueError:
        return await zelretch.delete(message, "Give me a valid number to spam.")

    to_spam = message.text.split(" ", 2)[2].strip()
    event = asyncio.Event()
    task = asyncio.create_task(
        spam_text(client, message.chat.id, to_spam, count, reply_to, None, None, event)
    )

    if spamTask.get(message.chat.id, None):
        spamTask[message.chat.id].append(event)
    else:
        spamTask[message.chat.id] = [event]

    await message.delete()
    await task


@on_message("dspam", allow_master=True)
async def delaySpam(client: Client, message: Message):
    if len(message.command) < 4:
        return await zelretch.delete(message, "Give me something to spam.")

    reply_to = message.reply_to_message.id if message.reply_to_message else None
    try:
        count = int(message.command[1])
    except ValueError:
        return await zelretch.delete(message, "Give me a valid number to spam.")

    try:
        delay = float(message.command[2])
    except ValueError:
        return await zelretch.delete(message, "Give me a valid delay to spam.")

    to_spam = message.text.split(" ", 3)[3].strip()
    event = asyncio.Event()
    task = asyncio.create_task(
        spam_text(client, message.chat.id, to_spam, count, reply_to, delay, None, event)
    )

    if spamTask.get(message.chat.id, None):
        spamTask[message.chat.id].append(event)
    else:
        spamTask[message.chat.id] = [event]

    await message.delete()
    await task


@on_message("mspam", allow_master=True)
async def mediaSpam(client: Client, message: Message):
    if not message.reply_to_message:
        return await zelretch.delete(message, "Reply to a media to spam.")

    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me a valid number to spam.")

    try:
        count = int(message.command[1])
    except ValueError:
        return await zelretch.delete(message, "Give me a valid number to spam.")

    copy_id = message.reply_to_message.id
    event = asyncio.Event()
    task = asyncio.create_task(
        spam_text(client, message.chat.id, None, count, None, None, copy_id, event)
    )

    if spamTask.get(message.chat.id, None):
        spamTask[message.chat.id].append(event)
    else:
        spamTask[message.chat.id] = [event]

    await message.delete()
    await task


@on_message("stopspam", allow_master=True)
async def stopSpam(_, message: Message):
    chat_id = message.chat.id

    if not spamTask.get(chat_id, None):
        return await zelretch.delete(message, "No spam task running for this chat.")

    for event in spamTask[chat_id]:
        event.set()

    chat_name = message.chat.title or message.chat.first_name
    del spamTask[chat_id]
    await zelretch.delete(message, f"Spam task stopped for {chat_name}.")


@on_message("listspam", allow_master=True)
async def listSpam(_, message: Message):
    active_spams = list(spamTask.keys())

    text = "**Active Spam Tasks:**\n\n"
    for active in active_spams:
        text += f"{Symbols.anchor} `{active}`\n"

    await zelretch.edit(message, text)


HelpMenu("spam").add(
    "spam",
    "<count> <message text>",
    "Send the given text message N times in rapid succession into the current chat.",
    "spam 10 hello",
    "Excessive spamming can trigger Telegram's flood protection and may get the userbot account restricted or banned.",
).add(
    "dspam",
    "<count> <delay (seconds)> <message text>",
    "Send the given text message N times with a fixed delay between each send. Useful for staying under Telegram's rate limits.",
    "dspam 10 1 hello",
    "Excessive spamming can still get the account restricted even with delays.",
).add(
    "mspam",
    "<count> <reply to media>",
    "Copy and resend the replied media message N times into the current chat.",
    "mspam 10",
    "Excessive spamming can trigger Telegram's flood protection.",
).add(
    "stopspam",
    None,
    "Immediately cancel every active spam task running in the current chat.",
    "stopspam",
    "Only affects the chat where the command is sent; other chats continue their tasks.",
).add(
    "listspam",
    None,
    "List every active spam task across all chats, showing the chat ID and remaining count for each.",
    "listspam",
).info(
    "Message spam tools — send text or media repeatedly, with optional delays, and the ability to stop tasks mid-run."
).done()

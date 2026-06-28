from kurigram import Client, filters
from kurigram.types import Message

from . import Config, HelpMenu, custom_handler, db, handler, zelretch, on_message


@on_message(["snip", "note"], allow_master=True)
async def addsnip(client: Client, message: Message):
    if len(message.command) < 2 or not message.reply_to_message:
        return await zelretch.delete(
            message,
            f"Reply to a message with {handler}snip <keyword> to save it as a snip.",
        )

    keyword = (await zelretch.input(message)).replace("#", "")
    kaleido = await zelretch.edit(message, f"Saving snip `#{keyword}`")
    msg = await message.reply_to_message.forward(Config.LOGGER_ID)

    await db.set_snip(client.me.id, message.chat.id, keyword.lower(), msg.id)
    await zelretch.delete(kaleido, f"**📌 𝖭𝖾𝗐 𝖲𝗇𝗂𝗉 𝖭𝗈𝗍𝖾 𝖲𝖺𝗏𝖾𝖽:** `#{keyword}`")
    await msg.reply_text(
        f"**📌 𝖭𝖾𝗐 𝖲𝗇𝗂𝗉 𝖭𝗈𝗍𝖾 𝖲𝖺𝗏𝖾𝖽:** `#{keyword}`\n\n**DO NOT DELETE THIS MESSAGE!!!**",
    )


@on_message(["rmsnip", "rmallsnip"], allow_master=True)
async def rmsnip(client: Client, message: Message):
    if len(message.command[0]) < 7:
        if len(message.command) < 2:
            return await zelretch.delete(message, "Give a snip note name to remove.")

        keyword = (await zelretch.input(message)).replace("#", "")
        kaleido = await zelretch.edit(message, f"Removing snip `#{keyword}`")

        if await db.is_snip(client.me.id, message.chat.id, keyword.lower()):
            await db.rm_snip(client.me.id, message.chat.id, keyword.lower())
            await zelretch.delete(kaleido, f"**🍀 𝖲𝗇𝗂𝗉 𝖭𝗈𝗍𝖾 𝖱𝖾𝗆𝗈𝗏𝖾𝖽:** `#{keyword}`")
        else:
            await zelretch.delete(kaleido, f"**🍀 𝖲𝗇𝗂𝗉 𝖭𝗈𝗍𝖾 𝖽𝗈𝖾𝗌 𝗇𝗈𝗍 𝖾𝗑𝗂𝗌𝗍𝗌:** `#{keyword}`")
    else:
        kaleido = await zelretch.edit(message, "Removing all snips...")
        await db.rm_all_snips(client.me.id, message.chat.id)
        await zelretch.delete(kaleido, "All snips have been removed.")


@on_message(["getsnip", "snips"], allow_master=True)
async def snips(client: Client, message: Message):
    if message.command[0][0] == "g":
        if len(message.command) < 2:
            return await zelretch.delete(message, "Give a snip note name to get.")

        keyword = await zelretch.input(message)
        kaleido = await zelretch.edit(message, f"Getting snip `#{keyword}`")

        if await db.is_snip(client.me.id, message.chat.id, keyword.lower()):
            data = await db.get_snip(client.me.id, message.chat.id, keyword.lower())
            msgid = None
            for s in data["snips"]:
                if s["keyword"] == keyword.lower():
                    msgid = s["msgid"]
                    break
            if msgid is None:
                return await zelretch.delete(kaleido, "Snip does not exist.")
            sent = await client.copy_message(message.chat.id, Config.LOGGER_ID, msgid)

            await sent.reply_text(f"**🍀 𝖲𝗇𝗂𝗉 𝖭𝗈𝗍𝖾:** `#{keyword}`")
            await kaleido.delete()
        else:
            await zelretch.delete(kaleido, f"**🍀 𝖲𝗇𝗂𝗉 𝖭𝗈𝗍𝖾 𝖽𝗈𝖾𝗌 𝗇𝗈𝗍 𝖾𝗑𝗂𝗌𝗍𝗌:** `#{keyword}`")

    else:
        kaleido = await zelretch.edit(message, "Getting all snips...")
        snips = await db.get_all_snips(client.me.id, message.chat.id)
        if snips:
            text = f"**🍀 𝖭𝗈. 𝗈𝖿 𝖲𝗇𝗂𝗉 𝖭𝗈𝗍𝖾 𝗂𝗇 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍:** `{len(snips)}`\n\n"

            for i, snip in enumerate(snips, 1):
                text += f"** {'0' if i < 10 else ''}{i}:** `#{snip['keyword']}`\n"

            await kaleido.edit(text)
        else:
            await zelretch.delete(kaleido, "No snip note saved in this chat.")


@custom_handler(
    filters.incoming & filters.regex(r"^#\s*(.*)$") & filters.text & ~filters.service
)
async def snipHandler(client: Client, message: Message):
    keyword = message.text.split("#", 1)[1].strip().lower()
    if await db.is_snip(client.me.id, message.chat.id, keyword):
        data = await db.get_snip(client.me.id, message.chat.id, keyword)
        msgid = None
        for s in data["snips"]:
            if s["keyword"] == keyword:
                msgid = s["msgid"]
                break
        if msgid is None:
            return await zelretch.delete(message, "Snip does not exist.")

        reply_to = (
            message.reply_to_message.id if message.reply_to_message else message.id
        )
        await client.copy_message(
            message.chat.id, Config.LOGGER_ID, msgid, reply_to_message_id=reply_to
        )


HelpMenu("snips").add(
    "snip",
    "<keyword> <reply to a message>",
    "Save the replied message as a snip (saved note). Anyone in the chat can trigger it by sending #<keyword>.",
    "snip rules",
    "Alias 'note' can also be used. Text, media, and documents are supported.",
).add(
    "rmsnip",
    "<keyword>",
    "Delete a single snip by its keyword.",
    "rmsnip rules",
).add(
    "rmallsnip",
    None,
    "Delete every saved snip in the current chat in one go.",
    "rmallsnip",
).add(
    "getsnip",
    "<keyword>",
    "Preview the saved snip message for a specific keyword without triggering the hashtag.",
    "getsnip rules",
).add(
    "snips",
    None,
    "List every snip keyword currently saved in the chat.",
    "snips",
).info(
    "Saved notes (snips) — store messages that can be recalled by sending #<keyword> in the chat."
).done()

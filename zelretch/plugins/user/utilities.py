import os

import requests
from kurigram.types import Message

from zelretch.core import ENV
from zelretch.functions.images import remove_bg
from zelretch.functions.paste import spaceBin

from . import Config, HelpMenu, db, zelretch, on_message

@on_message(["removebg", "rmbg"], allow_master=True)
async def removeBg(_, message: Message):
    api_key = await db.get_env(ENV.remove_bg_api)
    if not api_key:
        return await zelretch.delete(
            message, "To remove background you need to setup Remove BG Api key."
        )

    if message.reply_to_message:
        if (
            message.reply_to_message.document
            and message.reply_to_message.document.mime_type.lower().startswith("image")
        ):
            filename = await message.reply_to_message.download(Config.TEMP_DIR)
        elif message.reply_to_message.photo:
            filename = await message.reply_to_message.download(Config.TEMP_DIR)
        elif (
            message.reply_to_message.sticker
            and not message.reply_to_message.sticker.is_animated
            and not message.reply_to_message.sticker.is_video
        ):
            filename = await message.reply_to_message.download(Config.TEMP_DIR + "sticker.png")
        else:
            return await zelretch.delete(
                message, "Reply to an image or give the url to remove background."
            )
    elif len(message.command) >= 2:
        resp = requests.get(await zelretch.input(message))
        filename = f"{Config.TEMP_DIR}/{message.id}.png"

        with open(filename, "wb") as f:
            f.write(resp.content)
    else:
        return await zelretch.delete(
            message, "Reply to an image or give the url to remove background."
        )

    kaleido = await zelretch.edit(message, "Removing background...")

    try:
        removed_img = await remove_bg(api_key, filename)
        doc_file = await message.reply_document(
            removed_img,
            caption="💫 **Removed Background!**",
            force_document=True,
        )
        await doc_file.reply_photo(removed_img, caption="🖼️ **Preview!**")
        os.remove(filename)
        os.remove(removed_img)
    except Exception as e:
        await zelretch.error(kaleido, f"`{e}`")

@on_message("paste", allow_master=True)
async def paste_text(_, message: Message):
    kaleido = await zelretch.edit(message, "Pasting text...")
    text_to_paste = ""
    extention = "none"

    if len(message.command) >= 2:
        text_to_paste = await zelretch.input(message)
    elif message.reply_to_message.text:
        text_to_paste = message.reply_to_message.text
    elif message.reply_to_message.document:
        filename = await message.reply_to_message.download(Config.TEMP_DIR)
        with open(filename, "r") as f:
            text_to_paste = f.read()
        extention = filename.split(".")[-1]
        os.remove(filename)
    else:
        return await zelretch.delete(message, "Reply to a text to paste it.")

    try:
        await kaleido.edit(
            f"**📝 Pasted to:** {spaceBin(text_to_paste, extention)}",
            disable_web_page_preview=True,
        )
    except Exception as e:
        await zelretch.error(kaleido, f"`{e}`")

HelpMenu("utilities").add(
    "removebg",
    "<reply to image> or <image url>",
    "Remove the background from an image using the remove.bg API and upload the transparent PNG as a document, followed by a preview photo.",
    "removebg https://example.com/photo.png",
    "Alias 'rmbg' can also be used. Requires the REMOVE_BG_API variable — get a free key from https://www.remove.bg/api.",
).add(
    "paste",
    "<reply to message> or <text>",
    "Upload text to spaceb.in (or a fallback pastebin) and return a shareable URL. Accepts inline text, a reply to a text message, or a reply to a text file.",
    "paste",
).info(
    "Miscellaneous utilities — AI background removal and quick text pasting for code or notes."
).done()

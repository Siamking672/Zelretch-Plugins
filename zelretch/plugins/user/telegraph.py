import os
import uuid

from kurigram import Client
from kurigram.enums import MessageMediaType
from kurigram.types import Message

from zelretch.functions.images import convert_to_png
from zelretch.functions.utility import TGraph

from . import Config, HelpMenu, Symbols, zelretch, on_message


@on_message(["tgm", "tm"], allow_master=True)
async def telegraph_media(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.media:
        return await zelretch.edit(message, "__Reply to a media message!__")

    kaleido = await zelretch.edit(message, "__Uploading to telegraph...__")

    if message.reply_to_message.media in [
        MessageMediaType.ANIMATION,
        MessageMediaType.VIDEO,
    ]:
        file_size = (
            message.reply_to_message.animation.file_size
            if message.reply_to_message.animation
            else message.reply_to_message.video.file_size
        )

        if file_size >= 5242880:
            return await zelretch.delete(
                kaleido,
                "__This media is too big to upload to telegraph! You need to choose media below 5mb.__",
            )

        path = await message.reply_to_message.download(Config.TEMP_DIR)

    elif message.reply_to_message.media in [
        MessageMediaType.PHOTO,
        MessageMediaType.STICKER,
        MessageMediaType.DOCUMENT,
    ]:
        file_size = (
            message.reply_to_message.photo.file_size
            if message.reply_to_message.photo
            else message.reply_to_message.sticker.file_size
            if message.reply_to_message.sticker
            else message.reply_to_message.document.file_size
        )

        if file_size >= 5242880:
            return await zelretch.delete(
                kaleido,
                "__This media is too big to upload to telegraph! You need to choose media below 5mb.__",
            )

        if message.reply_to_message.document:
            if message.reply_to_message.document.mime_type.lower().split("/")[0] in [
                "image",
                "video",
            ]:
                path = await message.reply_to_message.download(Config.TEMP_DIR)
            else:
                return await zelretch.delete(kaleido, "This media is not supported!")
        else:
            path = await message.reply_to_message.download(Config.TEMP_DIR)
    else:
        return await zelretch.delete(kaleido, "This media is not supported!")

    if path.lower().endswith(".webp"):
        path = convert_to_png(path)

    await kaleido.edit(
        f"**Media downloaded to local server.** __Now uploading to telegraph...__"
    )

    try:
        media_url = TGraph.telegraph.upload_file(path)
        url = f"https://te.legra.ph{media_url[0]['src']}"
    except Exception as e:
        await zelretch.error(kaleido, str(e))
    else:
        await kaleido.edit(
            f"**💫 Uploaded to [telegraph]({url})!**\n\n**{Symbols.anchor} URL:** `{url}`",
            disable_web_page_preview=True,
        )

    os.remove(path)


@on_message(["tgt", "tt"], allow_master=True)
async def telegraph_text(client: Client, message: Message):
    if len(message.command) < 2:
        page_name = client.me.first_name
    else:
        page_name = await zelretch.input(message)

    if not message.reply_to_message:
        return await zelretch.edit(
            message, "__Reply to a message to upload it on telegraph page!__"
        )

    kaleido = await zelretch.edit(message, "__Uploading to telegraph...__")

    page_content = (
        message.reply_to_message.text or message.reply_to_message.caption or ""
    )

    media_list = None
    if message.reply_to_message.document:
        mime = message.reply_to_message.document.mime_type or ""
        if mime.startswith("text/"):
            page_media = await message.reply_to_message.download(Config.TEMP_DIR)
            with open(page_media, "r", encoding="utf-8", errors="ignore") as f:
                page_content += f.read() + "\n"
            os.remove(page_media)

    page_content = page_content.replace("\n", "<br>")

    try:
        response = TGraph.telegraph.create_page(page_name, html_content=page_content)
    except Exception:
        rnd_key = uuid.uuid4().hex[:8]
        page_name = f"{page_name}_{rnd_key}"
        response = TGraph.telegraph.create_page(page_name, html_content=page_content)

    try:
        url = f"https://te.legra.ph/{response['path']}"
        await kaleido.edit(
            f"**💫 Uploaded to [telegraph]({url})!**\n\n**{Symbols.anchor} URL:** `{url}`",
            disable_web_page_preview=True,
        )
    except Exception as e:
        await zelretch.error(kaleido, str(e))


HelpMenu("telegraph").add(
    "tgm",
    "<reply to media>",
    "Upload the replied photo or video to telegra.ph and return a direct URL that can be shared anywhere.",
    "tgm",
    "Alias 'tm' can also be used. Only photos and videos under 5 MB are supported by Telegraph.",
).add(
    "tgt",
    "<reply to message> <page title (optional)>",
    "Upload the replied message's text content to telegra.ph as a formatted article page and return the URL.",
    "tgt My Article Title",
    "Alias 'tt' can also be used. Markdown and HTML formatting in the original message are preserved.",
).info(
    "Telegraph uploader — host media and text articles on telegra.ph and share the direct links."
).done()

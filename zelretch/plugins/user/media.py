import os
import time

import requests
from PIL import Image
from kurigram.enums import MessageMediaType
from kurigram.types import Message

from zelretch.core import ENV
from zelretch.functions.convert import tgs_to_png, video_to_png
from zelretch.functions.formatter import readable_time
from zelretch.functions.images import create_thumbnail, draw_meme
from zelretch.functions.media import get_metedata
from zelretch.functions.paste import post_to_telegraph
from zelretch.functions.runtime import progress, runcmd
from zelretch.functions.utility import TGraph

from . import Config, HelpMenu, db, zelretch, on_message


@on_message("mediainfo", allow_master=True)
async def mediaInfo(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.media:
        return await zelretch.delete(message, "Reply to a media file")

    media = message.reply_to_message.media
    kaleido = await zelretch.edit(message, "Getting media info...")

    if media == MessageMediaType.ANIMATION:
        media_file = message.reply_to_message.animation
    elif media == MessageMediaType.AUDIO:
        media_file = message.reply_to_message.audio
    elif media == MessageMediaType.DOCUMENT:
        media_file = message.reply_to_message.document
    elif media == MessageMediaType.PHOTO:
        media_file = message.reply_to_message.photo
    elif media == MessageMediaType.STICKER:
        media_file = message.reply_to_message.sticker
    elif media == MessageMediaType.VIDEO:
        media_file = message.reply_to_message.video
    else:
        return await zelretch.delete(message, "Unsupported media type")

    metadata = await get_metedata(media_file)
    if not metadata:
        return await zelretch.delete(message, "Failed to get media info")

    await kaleido.edit(f"Fetched metadata, now fetching extra mediainfo...")

    start_time = time.time()
    try:
        file_path = await message.reply_to_message.download(
            Config.DWL_DIR,
            progress=progress,
            progress_args=(kaleido, start_time, "⬇️ Downloading"),
        )
    except Exception:
        return await kaleido.edit(
            f"**Failed to download media check the metadata instead!**\n\n{metadata}"
        )

    out, _, _, _ = await runcmd(f"mediainfo '{file_path}'")
    if not out:
        return await kaleido.edit(
            f"Failed to get mediainfo, check the metadata instead!\n\n{metadata}"
        )

    await kaleido.edit(f"Uploading mediainfo to telegraph...")

    to_paste = f"<strong>💫 Zelretch Media Info:</strong><br>{metadata}<br><b>📝 MediaInfo:</b><br><code>{out}</code>"
    link = post_to_telegraph("ZelretchMediaInfo", to_paste)

    await kaleido.edit(f"**📌 Media Info:** [Here]({link})", disable_web_page_preview=True)
    os.remove(file_path)


@on_message(["mmf", "memify"], allow_master=True)
async def memify(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Enter some text!")

    if not message.reply_to_message or not message.reply_to_message.media:
        return await zelretch.delete(message, "Reply to a media file")

    start_time = time.time()
    kaleido = await zelretch.edit(message, "Memifying...")
    file = await message.reply_to_message.download(
        Config.DWL_DIR,
        progress=progress,
        progress_args=(kaleido, start_time, "⬇️ Downloading"),
    )

    text = await zelretch.input(message)
    if ";" in text:
        upper_text, lower_text = text.split(";")
    else:
        upper_text, lower_text = text, ""

    if file and file.endswith(".tgs"):
        await kaleido.edit("Looks like an animated sticker, converting to image...")
        pic = await tgs_to_png(file)
    elif file and file.endswith((".webp", ".png")):
        pic = Image.open(file).save(file, "PNG", optimize=True)
    elif file:
        await kaleido.edit("Converting to image...")
        pic, status = await video_to_png(file, 0)
        if status == False:
            return await zelretch.error(kaleido, pic)
    else:
        return await zelretch.delete(message, "Unsupported media type")

    await kaleido.edit("Adding text...")
    memes = await draw_meme(file, upper_text, lower_text)

    await zelretch.delete(kaleido, "Done!")
    await message.reply_sticker(memes[1])
    await message.reply_photo(
        memes[0],
        caption=f"**🍀 Memified.**",
    )

    os.remove(pic)
    os.remove(file)
    os.remove(memes[0])
    os.remove(memes[1])


@on_message("setthumbnail", allow_master=True)
async def set_thumbnail(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(
            message, "Reply to a media file to set as thumbnail!"
        )

    if not message.reply_to_message or not message.reply_to_message.media:
        return await zelretch.delete(
            message, "Reply to a media file to set as thumbnail!"
        )

    media = message.reply_to_message.media
    if media not in MessageMediaType.PHOTO:
        return await zelretch.delete(
            message,
            "Only photos are supported! If this is a file, try converting it to a photo first.",
        )

    if message.reply_to_message.photo.file_size >= 5242880:
        return await zelretch.delete(
            message,
            "This photo is too big to upload to telegraph! You need to choose a photo below 5mb.",
        )

    kaleido = await zelretch.edit(message, "Uploading to telegraph...")
    path = await message.reply_to_message.download(Config.TEMP_DIR)

    try:
        media_url = TGraph.telegraph.upload_file(path)
        url = f"https://te.legra.ph{media_url[0]['src']}"
    except Exception as e:
        return await zelretch.error(kaleido, str(e))

    await db.set_env(ENV.thumbnail_url)
    await zelretch.delete(kaleido, f"Thumbnail set to [this image]({url})!", 20)
    os.remove(path)


@on_message("rename", allow_master=True)
async def renameMedia(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.media:
        return await zelretch.delete(message, "Reply to a media file to rename it!")

    media = message.reply_to_message.media
    if media not in [
        MessageMediaType.AUDIO,
        MessageMediaType.DOCUMENT,
        MessageMediaType.PHOTO,
        MessageMediaType.VIDEO,
        MessageMediaType.VOICE,
        MessageMediaType.ANIMATION,
        MessageMediaType.STICKER,
        MessageMediaType.VIDEO_NOTE,
    ]:
        return await zelretch.delete(message, "Unsupported media type!")

    if len(message.command) < 2:
        return await zelretch.delete(
            message, "You need to provide a new filename with extention!"
        )

    new_name = await zelretch.input(message)
    kaleido = await zelretch.edit(message, f"Renaming to `{new_name}` ...")

    strart_time = time.time()
    renamed_file = await message.reply_to_message.download(
        Config.DWL_DIR + new_name,
        progress=progress,
        progress_args=(kaleido, strart_time, "⬇️ Downloading"),
    )

    dwl_time = readable_time(int(strart_time - time.time()))
    await kaleido.edit(f"**Downloaded and Renamed in** `{dwl_time}`**,** __uploading...__")

    start2 = time.time()

    thumb = await db.get_env(ENV.thumbnail_url)
    if thumb:
        binary = requests.get(thumb).content
        photo = f"{Config.TEMP_DIR}/thumb_{int(time.time())}.jpeg"
        with open(photo, "wb") as f:
            f.write(binary)
        thumbnail = create_thumbnail(photo, (320, 320), 199)
    else:
        photo = None
        thumbnail = None

    await message.reply_document(
        renamed_file,
        thumb=thumbnail,
        caption=f"**📁 File Name:** `{new_name}`",
        file_name=new_name,
        force_document=True,
        progress=progress,
        progress_args=(kaleido, start2, "⬆️ Uploading"),
    )

    end_time = readable_time(int(start2 - time.time()))
    total_time = readable_time(int(strart_time - time.time()))
    await kaleido.edit(
        f"**📁 File Name:** `{new_name}`\n\n**⬇️ Downloaded in:** `{dwl_time}`\n**⬆️ Uploaded in:** `{end_time}`\n**💫 Total time taken:** `{total_time}`"
    )
    os.remove(renamed_file)
    if photo:
        os.remove(photo)


HelpMenu("media").add(
    "mediainfo",
    "<reply to media message>",
    "Fetch and display the metadata of the replied media file, including codec, resolution, duration, bitrate, and stream information via mediainfo.",
    "mediainfo",
).add(
    "memify",
    "<reply to media> <upper text>;<lower text>",
    "Overlay meme-style caption text on the replied photo or sticker. Use a semicolon to separate upper and lower captions.",
    "memify TOP;BOTTOM",
    "When ';' is omitted, all text is rendered as the upper caption only.",
).add(
    "rename",
    "<reply to media file> <new filename with extension>",
    "Re-upload the replied media file with a new filename. The extension must be included and should match the file's actual type.",
    "rename zelretch.jpg",
).add(
    "setthumbnail",
    "<reply to photo>",
    "Set the replied photo as the default thumbnail for all subsequent file uploads performed by the bot (e.g. via the rename command).",
    "setthumbnail",
    "The photo must be sent as a compressed photo (not as a document) and be under 5 MB.",
).info(
    "Media utilities — inspect metadata, add meme captions, rename files, and configure upload thumbnails."
).done()

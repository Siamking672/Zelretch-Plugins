import os
import time
import zipfile

from kurigram.types import Message

from zelretch.functions.formatter import readable_time
from zelretch.functions.runtime import get_files_from_directory, progress

from . import Config, HelpMenu, zelretch, on_message


@on_message("zip", allow_master=True)
async def zip_files(_, message: Message):
    if not message.reply_to_message:
        return await zelretch.delete(message, "Reply to a message to zip it.")

    media = message.reply_to_message.media
    if not media:
        return await zelretch.delete(message, "Reply to a media message to zip it.")

    kaleido = await zelretch.edit(message, "`Zipping...`")
    start = time.time()
    download_path = await message.reply_to_message.download(
        f"{Config.TEMP_DIR}temp_{round(time.time())}",
        progress=progress,
        progress_args=(kaleido, start, "📦 Zipping"),
    )

    zip_path = Config.TEMP_DIR + f"zipped_{int(time.time())}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(download_path, arcname=os.path.basename(download_path))

    await zelretch.delete(kaleido, "Zipped Successfully.")
    await message.reply_document(
        zip_path,
        caption=f"**Zipped in {readable_time(time.time() - start)}.**",
        progress=progress,
        progress_args=(kaleido, start, "⬆️ Uploading"),
    )

    os.remove(zip_path)
    os.remove(download_path)


@on_message("unzip", allow_master=True)
async def unzip_file(_, message: Message):
    if not message.reply_to_message:
        return await zelretch.delete(message, "Reply to a message to unzip it.")

    media = message.reply_to_message.media
    if not media:
        return await zelretch.delete(message, "Reply to a media message to unzip it.")

    kaleido = await zelretch.edit(message, "`Unzipping...`")
    start = time.time()
    download_path = await message.reply_to_message.download(
        f"{Config.TEMP_DIR}temp_{round(time.time())}",
        progress=progress,
        progress_args=(kaleido, start, "📦 Unzipping"),
    )

    try:
        with zipfile.ZipFile(download_path, "r") as zip_file:
            if not os.path.isdir(Config.TEMP_DIR + "unzipped/"):
                os.mkdir(Config.TEMP_DIR + "unzipped/")
            zip_file.extractall(Config.TEMP_DIR + "unzipped/")
    except zipfile.BadZipFile:
        os.remove(download_path)
        return await zelretch.delete(kaleido, "That file is not a valid zip archive.")

    await zelretch.delete(kaleido, "Unzipped Successfully.")
    files = await get_files_from_directory(Config.TEMP_DIR + "unzipped/")

    for file in files:
        if os.path.exists(file):
            try:
                await message.reply_document(
                    file,
                    caption=f"**Unzipped {os.path.basename(file)}.**",
                    force_document=True,
                    progress=progress,
                    progress_args=(kaleido, start, "⬆️ Uploading"),
                )
            except Exception as e:
                await message.reply_text(f"**{file}:** `{e}`")
                continue
            os.remove(file)

    os.remove(download_path)


HelpMenu("archiver").add(
    "zip",
    "<reply to media>",
    "Compress the replied media file into a .zip archive and upload it back to the chat.",
    "zip",
).add(
    "unzip",
    "<reply to a zip file>",
    "Extract the contents of a replied .zip archive and upload each file individually.",
    "unzip",
).info(
    "Compress and extract .zip archives directly inside Telegram."
).done()

import os
import time

from kurigram.types import Message

from zelretch.functions.convert import convert_to_gif
from zelretch.functions.runtime import runcmd

from . import HelpMenu, zelretch, on_message, Config


@on_message("stog", allow_master=True)
async def sticker_to_gif(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.sticker:
        return await zelretch.delete(
            message, "Reply to an animated/video sticker to convert it to gif."
        )

    kaleido = await zelretch.edit(message, "Converting ...")

    replied_sticker = message.reply_to_message.sticker

    if replied_sticker.is_animated:
        is_video = False
    elif replied_sticker.is_video:
        is_video = True
    else:
        return await zelretch.delete(kaleido, "Reply to an animated/video sticker.")

    dwl_path = await message.reply_to_message.download(Config.TEMP_DIR)
    gif_path = await convert_to_gif(dwl_path, is_video)

    await message.reply_animation(gif_path)
    await zelretch.delete(kaleido, "Converted to gif successfully!")

    os.remove(dwl_path)
    os.remove(gif_path)


@on_message("stoi", allow_master=True)
async def sticker_to_image(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.sticker:
        return await zelretch.delete(
            message, "Reply to an sticker to convert it to image."
        )

    kaleido = await zelretch.edit(message, "Converting ...")
    fileName = f"image_{round(time.time())}.png"
    dwl_path = await message.reply_to_message.download(f"{Config.TEMP_DIR}{fileName}")

    await message.reply_photo(dwl_path)
    await zelretch.delete(kaleido, "Converted to image successfully!")

    os.remove(dwl_path)


@on_message("itos", allow_master=True)
async def image_to_sticker(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await zelretch.delete(
            message, "Reply to an image to convert it to sticker."
        )

    kaleido = await zelretch.edit(message, "Converting ...")
    fileName = f"sticker_{round(time.time())}.webp"
    dwl_path = await message.reply_to_message.download(f"{Config.TEMP_DIR}{fileName}")

    await message.reply_sticker(dwl_path)
    await zelretch.delete(kaleido, "Converted to sticker successfully!")

    os.remove(dwl_path)


@on_message("ftoi", allow_master=True)
async def file_to_image(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await zelretch.delete(message, "Reply to a file to convert it to image.")

    if message.reply_to_message.document.mime_type.split("/")[0] != "image":
        return await zelretch.delete(message, "Reply to an image file.")

    kaleido = await zelretch.edit(message, "Converting ...")
    fileName = f"image_{round(time.time())}.png"
    dwl_path = await message.reply_to_message.download(f"{Config.TEMP_DIR}{fileName}")

    await message.reply_photo(dwl_path)
    await zelretch.delete(kaleido, "Converted to image successfully!")

    os.remove(dwl_path)


@on_message("itof", allow_master=True)
async def image_to_file(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await zelretch.delete(message, "Reply to an image to convert it to file.")

    kaleido = await zelretch.edit(message, "Converting ...")
    fileName = f"file_{round(time.time())}.png"
    dwl_path = await message.reply_to_message.download(f"{Config.TEMP_DIR}{fileName}")

    await message.reply_document(dwl_path)
    await zelretch.delete(kaleido, "Converted to file successfully!")

    os.remove(dwl_path)


@on_message("tovoice", allow_master=True)
async def media_to_voice(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.media:
        return await zelretch.delete(message, "Reply to a media to convert it to voice.")

    kaleido = await zelretch.edit(message, "Converting ...")
    dwl_path = await message.reply_to_message.download(f"{Config.TEMP_DIR}")
    voice_path = f"{round(time.time())}.ogg"

    cmd_list = [
        "ffmpeg",
        "-i",
        dwl_path,
        "-map",
        "0:a",
        "-codec:a",
        "libopus",
        "-b:a",
        "100k",
        "-vbr",
        "on",
        voice_path,
    ]

    _, err, _, _ = await runcmd(" ".join(cmd_list))

    if os.path.exists(voice_path):
        await message.reply_voice(voice_path)
        await zelretch.delete(kaleido, "Converted to voice successfully!")
        os.remove(voice_path)
    else:
        await zelretch.error(kaleido, f"`{err}`")

    os.remove(dwl_path)


@on_message("tomp3", allow_master=True)
async def media_to_mp3(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.media:
        return await zelretch.delete(message, "Reply to a media to convert it to mp3.")

    kaleido = await zelretch.edit(message, "Converting ...")
    dwl_path = await message.reply_to_message.download(f"{Config.TEMP_DIR}")
    mp3_path = f"{round(time.time())}.mp3"

    cmd_list = [
        "ffmpeg",
        "-i",
        dwl_path,
        "-vn",
        mp3_path,
    ]

    _, stderr, _, _ = await runcmd(" ".join(cmd_list))

    if os.path.exists(mp3_path):
        await message.reply_audio(mp3_path)
        await zelretch.delete(kaleido, "Converted to mp3 successfully!")
        os.remove(mp3_path)
    else:
        await zelretch.error(kaleido, f"`{stderr}`")

    os.remove(dwl_path)


HelpMenu("convert").add(
    "stog",
    "<reply to sticker>",
    "Convert an animated or video sticker into a GIF animation.",
    None,
    "Currently disabled — pending a fix for animated sticker extraction.",
).add(
    "stoi",
    "<reply to sticker>",
    "Convert a static sticker into a PNG image.",
    None,
    "Works only on static (non-animated, non-video) stickers.",
).add(
    "itos",
    "<reply to image>",
    "Convert an image into a sticker that can be added to a pack.",
    None,
    "Works on photos and image files up to 512x512 pixels.",
).add(
    "ftoi",
    "<reply to file>",
    "Send an image file (sent as a document) as a compressed photo instead.",
    None,
    "The file must be a valid image; non-image files cannot be converted.",
).add(
    "itof",
    "<reply to image>",
    "Send a compressed photo as a document, preserving full resolution and quality.",
    None,
    "Useful when you want to share an image without Telegram re-encoding it.",
).add(
    "tovoice",
    "<reply to audio/video>",
    "Convert an audio or video file into a Telegram voice note (round audio message).",
    None,
    "Only audio and video files can be converted to voice notes.",
).add(
    "tomp3",
    "<reply to audio/video>",
    "Extract or transcode the audio track of a media file into MP3 format.",
    None,
    "Works on both audio files and the audio track of video files.",
).info(
    "Convert media between sticker, image, file, voice, and MP3 formats."
).done()

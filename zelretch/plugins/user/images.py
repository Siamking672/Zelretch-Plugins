import io
import os
import time
from shutil import rmtree

import requests
from glitch_this import ImageGlitcher
from PIL import Image
from kurigram.enums import MessageMediaType
from kurigram.types import InputMediaDocument, InputMediaPhoto, Message

from zelretch.core import ENV
from zelretch.functions.images import deep_fry, download_images, get_wallpapers
from zelretch.functions.runtime import runcmd

from . import Config, HelpMenu, db, zelretch, on_message


def _chunk(images: list[str]) -> list[list]:
    return [images[i : i + 10] for i in range(0, len(images), 10)]


@on_message(["image", "img"], allow_master=True)
async def searchImage(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Provide a search query.")

    limit = 5
    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Searching...")

    if ";" in query:
        try:
            query, limit = query.split(";", 1)
        except:
            pass

    to_send = []
    images = await download_images(query.strip(), int(limit))

    for image in images:
        to_send.append(InputMediaPhoto(image))

    if to_send:
        if len(to_send) > 10:
            for chunk in _chunk(to_send):
                await kaleido.reply_media_group(chunk)
        else:
            await kaleido.reply_media_group(to_send)

        await zelretch.delete(kaleido, "Uploaded!")
    else:
        await zelretch.delete(kaleido, "No images found.")

    try:
        rmtree("./images")
    except:
        pass


@on_message("wallpaper", allow_master=True)
async def searchWallpaper(_, message: Message):
    if len(message.command) < 2:
        random = True
        query = ""
    else:
        random = False
        query = await zelretch.input(message)

    to_send = []
    limit = 10
    kaleido = await zelretch.edit(message, "Processing...")

    access = await db.get_env(ENV.unsplash_api)
    if not access:
        return await zelretch.delete(kaleido, "Unsplash API not found.")

    if ";" in query:
        try:
            query, limit = query.split(";", 1)
            limit = int(limit)
        except:
            pass

    if limit > 30:
        return await zelretch.delete(kaleido, "Limit should be less than 30.")
    elif limit < 1:
        return await zelretch.delete(kaleido, "Limit should be greater than 0.")

    wallpapers = await get_wallpapers(access, limit, query, random)
    if not wallpapers:
        return await zelretch.delete(kaleido, "No wallpapers found.")

    trash = []
    for i, wallpaper in enumerate(wallpapers):
        file_name = f"{i}_{int(time.time())}.jpg"
        with open(file_name, "wb") as f:
            f.write(requests.get(wallpaper).content)
        to_send.append(InputMediaDocument(file_name))
        trash.append(file_name)

    await kaleido.reply_media_group(to_send)
    await zelretch.delete(kaleido, "Uploaded!")
    [os.remove(trash_file) for trash_file in trash]


@on_message("glitch", allow_master=True)
async def glitcher(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.media:
        return await zelretch.delete(message, "Reply to a media message to glitch it.")

    kaleido = await zelretch.edit(message, "Glitching...")
    media = message.reply_to_message.media

    intensity = 2
    if len(message.command) > 1:
        intensity = int(message.command[1]) if message.command[1].isdigit() else 2

    if not 0 < intensity < 9:
        await kaleido.edit("intensity should be between 1 and 8... now glitching at 8")

    if media and media not in [
        MessageMediaType.ANIMATION,
        MessageMediaType.VIDEO,
        MessageMediaType.PHOTO,
        MessageMediaType.STICKER,
    ]:
        return await zelretch.delete(kaleido, "Only media messages are supported.")

    glitch_img = os.path.join(Config.TEMP_DIR, "glitch.png")
    dwl_path = await message.reply_to_message.download(Config.DWL_DIR)

    if dwl_path.endswith(".tgs"):
        cmd = f"lottie_convert.py --frame 0 -if lottie -of png {dwl_path} {glitch_img}"
        stdout, stderr, _, _ = await runcmd(cmd)
        if not os.path.lexists(glitch_img):
            return await zelretch.error(kaleido, f"`{stdout}`\n`{stderr}`")
    elif dwl_path.endswith(".webp"):
        os.rename(dwl_path, glitch_img)
        if not os.path.lexists(glitch_img):
            return await zelretch.error(kaleido, "File not found.")
    elif media in [MessageMediaType.VIDEO, MessageMediaType.ANIMATION]:
        cmd = f"ffmpeg -ss 0 -i {dwl_path} -vframes 1 {glitch_img}"
        stdout, stderr, _, _ = await runcmd(cmd)
        if not os.path.lexists(glitch_img):
            return await zelretch.error(kaleido, f"`{stdout}`\n`{stderr}`")
    else:
        os.rename(dwl_path, glitch_img)
        if not os.path.lexists(glitch_img):
            return await zelretch.error(kaleido, "File not found.")

    glitcher = ImageGlitcher()
    img = Image.open(glitch_img)
    glitch = glitcher.glitch_image(img, intensity, color_offset=True, gif=True)

    output_path = os.path.join(Config.TEMP_DIR, "glitch.gif")
    glitch[0].save(
        fp=output_path,
        format="GIF",
        append_images=glitch[1:],
        save_all=True,
        duration=200,
        loop=0,
    )

    await message.reply_animation(output_path)
    await zelretch.delete(kaleido, f"Glitched at intensity {intensity}")
    os.remove(output_path)
    os.remove(glitch_img)
    try:
        os.remove(dwl_path)
    except BaseException:
        pass


@on_message("deepfry", allow_master=True)
async def deepfry(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await zelretch.delete(message, "Reply to a photo to deepfry it.")

    if len(message.command) > 1:
        try:
            quality = int(message.command[1])
        except ValueError:
            quality = 2
    else:
        quality = 2

    kaleido = await zelretch.edit(message, "Deepfrying...")
    photo = await message.reply_to_message.download(Config.DWL_DIR)

    if quality > 9:
        quality = 9
    elif quality < 1:
        quality = 2

    image = Image.open(photo)
    for _ in range(quality):
        image = await deep_fry(image)

    fried = io.BytesIO()
    fried.name = "deepfried.jpeg"
    image.save(fried, "JPEG")
    fried.seek(0)

    await kaleido.reply_photo(fried)
    await zelretch.delete(kaleido, "Deepfried!")

    os.remove(photo)


HelpMenu("images").add(
    "image",
    "<query> ; <limit (optional)>",
    "Search Google Images for the query and upload the top results into the chat. Separate the query and the optional limit with a semicolon.",
    "image zelretch ; 5",
    "Alias 'img' can also be used. Default limit is 3 images when omitted.",
).add(
    "wallpaper",
    "<query> ; <limit (optional)>",
    "Search Unsplash for high-quality wallpapers matching the query. If no query is given, random wallpapers are uploaded.",
    "wallpaper tokyo street ; 5",
    "Requires the UNSPLASH_API variable. Get a free key from https://unsplash.com/join.",
).add(
    "glitch",
    "<reply to media> <intensity (1-8, optional)>",
    "Apply a glitch-art effect to the replied sticker, GIF, photo, or video. Higher intensity produces more distortion.",
    "glitch 4",
    "Intensity defaults to 2. Accepts integers from 1 to 8.",
).add(
    "deepfry",
    "<reply to photo> <quality (1-9, optional)>",
    "Apply a deep-fried meme effect to the replied photo — oversaturated, noisy, and crunchy. Higher quality values intensify the effect.",
    "deepfry 5",
    "Quality defaults to 2. Accepts integers from 1 to 9.",
).info(
    "Image search and manipulation — Google Images, Unsplash wallpapers, glitch art, and deep-fry effects."
).done()

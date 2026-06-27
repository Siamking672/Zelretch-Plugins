import os
import time

import requests
from kurigram.types import Message

from zelretch.core import ENV
from zelretch.functions.formatter import readable_time
from zelretch.functions.images import get_wallpapers, make_logo

from . import Config, HelpMenu, db, zelretch, on_message


@on_message("logo", allow_master=True)
async def makeLogo(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Provide a text to make a logo.")

    start_time = time.time()
    kaleido = await zelretch.edit(message, "Processing...")
    query = await zelretch.input(message)

    if message.reply_to_message and message.reply_to_message.photo:
        photo = await message.reply_to_message.download(Config.TEMP_DIR + "temp_bg.jpg")
        text = query
    else:
        if "--" in query:
            text, theme = query.split("--", 1)
            isRandom = False
        else:
            text, theme = query, ""
            isRandom = True

        access = await db.get_env(ENV.unsplash_api)
        if not access:
            return await zelretch.delete(
                kaleido, "Unsplash API not found. Either set it or reply to an image."
            )

        photo = await get_wallpapers(access, 1, theme.strip(), isRandom)
        if not photo:
            return await zelretch.delete(kaleido, "No wallpapers found.")

        binary = requests.get(photo[0]).content
        with open(Config.TEMP_DIR + "temp_bg.jpg", "wb") as f:
            f.write(binary)

    logo_path = await make_logo(Config.TEMP_DIR + "temp_bg.jpg", text.strip(), Config.FONT_PATH)
    time_taken = readable_time(int(time.time() - start_time))

    await message.reply_photo(
        logo_path,
        caption=f"**𝖫𝗈𝗀𝗈 𝖬𝖺𝖽𝖾 𝗂𝗇:** `{time_taken}`",
    )
    await kaleido.delete()
    os.remove(logo_path)


@on_message("setfont", allow_master=True)
async def setFont(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await zelretch.delete(message, "Reply to a font file to save it.")

    kaleido = await zelretch.edit(message, "Processing...")
    font = await message.reply_to_message.download(Config.DWL_DIR)

    if not font.endswith(".ttf"):
        return await zelretch.delete(kaleido, "Invalid font file. Only .ttf is supported.")

    if not os.path.exists(font):
        return await zelretch.delete(kaleido, "Font not found.")

    Config.FONT_PATH = font
    await zelretch.delete(kaleido, "Font set successfully.")


@on_message("resetfont", allow_master=True)
async def resetFont(_, message: Message):
    prev_font = Config.FONT_PATH
    if prev_font == "./zelretch/resources/fonts/Montserrat.ttf":
        return await zelretch.delete(message, "Font is already set to default.")

    Config.FONT_PATH = "./zelretch/resources/fonts/Montserrat.ttf"
    await zelretch.delete(message, "Font reset successfully.")
    os.remove(prev_font)


HelpMenu("logo").add(
    "logo",
    "<text> or <reply to image> <text>",
    "Generate a stylised logo image from the given text. A background image is fetched from Unsplash matching the optional theme, then the text is rendered on top using the configured font.",
    "logo Zelretch --supra",
    "Append '--<theme>' after the text to bias the Unsplash search (e.g. --supra, --cyberpunk, --forest). Requires the UNSPLASH_API variable.",
).add(
    "setfont",
    "<reply to a .ttf file>",
    "Override the default Montserrat font with a custom TrueType font for logo generation. The override lasts until the bot restarts.",
    "setfont",
    "Only .ttf files are supported.",
).add(
    "resetfont",
    None,
    "Revert to the built-in default Montserrat font, discarding any custom font set via 'setfont'.",
    "resetfont",
).info(
    "Generate text-on-background logo images with custom fonts and Unsplash-sourced backgrounds."
).done()

import os
import random
import time

from kurigram import Client
from kurigram.types import Message

from zelretch import START_TIME
from zelretch.core import ENV
from zelretch.functions.formatter import readable_time
from zelretch.functions.images import generate_alive_image
from zelretch.functions.templates import alive_template, ping_template

from . import Config, HelpMenu, db, zelretch, on_message


@on_message("alive", allow_master=True)
async def alive(client: Client, message: Message):
    kaleido = await zelretch.edit(message, "Charging mana...")

    img = await db.get_env(ENV.alive_pic)
    if not img:
        if message.from_user.photo:
            user_pfp = await client.download_media(message.from_user.photo.big_file_id)
            del_path = True
        else:
            user_pfp = "./zelretch/resources/images/zelretch_logo.png"
            del_path = False
        img = [
            generate_alive_image(
                message.from_user.first_name, user_pfp, del_path, Config.FONT_PATH
            )
        ]
    else:
        img = img.split(" ")

    img = random.choice(img)
    uptime = readable_time(time.time() - START_TIME)
    caption = await alive_template(client.me.first_name, uptime)

    if img.endswith(".mp4"):
        await message.reply_video(img, caption=caption)
    else:
        await message.reply_photo(img, caption=caption)
    await kaleido.delete()

    try:
        os.remove(img)
    except:
        pass


@on_message("ping", allow_master=True)
async def ping(client: Client, message: Message):
    start_time = time.time()
    kaleido = await zelretch.edit(message, "**Gandr fired...**")
    uptime = readable_time(time.time() - START_TIME)
    img = await db.get_env(ENV.ping_pic)
    end_time = time.time()
    speed = end_time - start_time
    caption = await ping_template(round(speed, 3), uptime, client.me.mention)
    if img:
        img = random.choice(img.split(" "))
        if img.endswith(".mp4"):
            await message.reply_video(
                img,
                caption=caption,
            )
        else:
            await message.reply_photo(
                img,
                caption=caption,
            )
            await kaleido.delete()
        return
    await zelretch.edit(kaleido, caption, no_link_preview=True)


@on_message("history", allow_master=True)
async def history(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await zelretch.delete(
                message, "Either reply to an user or give me a username to get history."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{str(e)}`")
    else:
        user = message.reply_to_message.from_user

    kaleido = await zelretch.edit(message, "Charging mana...")

    try:
        response = await client.ask("@SangMata_BOT", f"{user.id}", timeout=60)
    except Exception as e:
        return await zelretch.error(kaleido, f"`{str(e)}`")

    if "you have used up your quota for today" in response.text:
        return await zelretch.delete(
            kaleido,
            f"Your quota of using SangMata Bot is over. Wait till 00:00 UTC before using it again.",
        )

    try:
        await response.delete()
        await response.request.delete()
    except:
        pass

    await zelretch.edit(kaleido, response.text)


@on_message("template", allow_master=True)
async def template_example(_, message: Message):
    variable_names = list(Config.TEMPLATES.keys())
    if len(message.command) < 2:
        return await zelretch.delete(
            message,
            f"__Give a template name to get template example.__\n\n**Available Templates:**\n`{'`,    `'.join(variable_names)}`",
            30,
        )

    if message.command[1].upper() not in variable_names:
        return await zelretch.delete(
            message,
            f"__Invalid template name:__ `{message.command[1].upper()}`\n\n**Available Templates:**\n`{'`,    `'.join(variable_names)}`",
            30,
        )

    await zelretch.edit(
        message,
        f"**{message.command[1].upper()} Template Example:**\n\n```{Config.TEMPLATES[message.command[1].upper()]}```"
    )


HelpMenu("bot").add(
    "alive",
    None,
    "Display the Rin Tohsaka-themed alive card showing the bot's version, uptime, and bound masters.",
    "alive",
    "Customise the picture and text using the 'ALIVE_PIC' and 'ALIVE_TEMPLATE' variables via the setvar command.",
).add(
    "ping",
    None,
    "Fire a Gandr shot and report the response latency and current uptime.",
    "ping",
    "Customise the picture and text using the 'PING_PIC' and 'PING_TEMPLATE' variables.",
).add(
    "history",
    "<reply to user> or <username/id>",
    "Fetch the username and display-name history of a user via the SangMata info bot.",
    "history @ZelretchUser",
    "SangMata must be running and reachable for this command to work.",
).add(
    "template",
    "<template name (optional)>",
    "Show the layout of a customisable template, or list every available template name when no argument is given.",
    "template alive_templates",
    "Use this to preview the placeholders you can use with the setvar command.",
).info(
    "Core Kaleidoscope commands — status, latency, user history, and template preview."
).done()

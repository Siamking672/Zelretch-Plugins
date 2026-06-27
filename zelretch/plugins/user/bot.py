import os
import random
import time

from pyrogram import Client
from pyrogram.types import Message

from zelretch import START_TIME
from zelretch.core import ENV
from zelretch.functions.formatter import readable_time
from zelretch.functions.images import generate_alive_image
from zelretch.functions.templates import alive_template, ping_template

from . import Config, HelpMenu, db, zelretch, on_message


@on_message("alive", allow_master=True)
async def alive(client: Client, message: Message):
    hell = await zelretch.edit(message, "Charging mana...")

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
    await hell.delete()

    try:
        os.remove(img)
    except:
        pass


@on_message("ping", allow_master=True)
async def ping(client: Client, message: Message):
    start_time = time.time()
    hell = await zelretch.edit(message, "**Gandr fired...**")
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
            await hell.delete()
        return
    await zelretch.edit(hell, caption, no_link_preview=True)


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

    hell = await zelretch.edit(message, "Charging mana...")

    try:
        response = await client.ask("@SangMata_BOT", f"{user.id}", timeout=60)
    except Exception as e:
        return await zelretch.error(hell, f"`{str(e)}`")

    if "you have used up your quota for today" in response.text:
        return await zelretch.delete(
            hell,
            f"Your quota of using SangMata Bot is over. Wait till 00:00 UTC before using it again.",
        )

    try:
        await response.delete()
        await response.request.delete()
    except:
        pass

    await zelretch.edit(hell, response.text)


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
    "Show the Rin-themed alive card for Zelretch.",
    "alive",
    "You can also customize alive message with suitable variables for it.",
).add(
    "ping",
    None,
    "Fire a Gandr ping and show latency plus uptime.",
    "ping",
    "You can also customize ping message by adding a media to it.",
).add(
    "history",
    "<reply to user>/<username/id>",
    "Get the username, name history of an user.",
    "history @ForGo10_God",
    "This command uses SangMata Bot to get the history.",
).add(
    "template",
    "<template name>",
    "Get the example of a template.",
    "template alive_templates",
    "This command is used to get the example of a template and a list of customisable templates.",
).info(
    "Kaleidoscope Core"
).done()

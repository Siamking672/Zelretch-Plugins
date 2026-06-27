import asyncio
import os

from pyrogram.types import Message

from zelretch.functions.driver import Driver

from . import HelpMenu, zelretch, on_message


@on_message("carbon", allow_master=True)
async def carbon(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me some code to make carbon.")

    code = await zelretch.input(message)
    hell = await zelretch.edit(message, "**[ 50% ]** __Making carbon...__")

    driver, resp = Driver.get()
    if not driver:
        return await zelretch.error(message, resp)

    await hell.edit("**[ 75% ]** __Making carbon...__")
    image = await Driver.generate_carbon(driver, code)
    await asyncio.sleep(4)

    await hell.edit("**[ 100% ]** __Uploading carbon...__")
    Driver.close(driver)

    await hell.reply_photo(image, caption=f"**𝖢𝖺𝗋𝖻𝗈𝗇𝖾𝖽:**\n`{code}`")
    await hell.delete()
    os.remove(image)


@on_message("karbon", allow_master=True)
async def karbon(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me some code to make karbon.")

    code = await zelretch.input(message)
    hell = await zelretch.edit(message, "**[ 50% ]** __Making karbon...__")

    driver, resp = Driver.get()
    if not driver:
        return await zelretch.error(message, resp)

    await hell.edit("**[ 75% ]** __Making karbon...__")
    image = await Driver.generate_carbon(driver, code, True)
    await asyncio.sleep(4)

    await hell.edit("**[ 100% ]** __Uploading karbon...__")
    Driver.close(driver)

    await hell.reply_photo(image, caption=f"**𝖢𝖺𝗋𝖻𝗈𝗇𝖾𝖽:**\n`{code}`")
    await hell.delete()
    os.remove(image)


HelpMenu("carbon").add(
    "carbon",
    "<code snippet>",
    "Makes carbon of given code snippet.",
    "carbon print('Hello World!')",
    "The style is fixed and cannot be changed.",
).add(
    "karbon",
    "<code snippet>",
    "Makes carbon of given code snippet.",
    "karbon print('Hello World!')",
    "The style is randomly choosed.",
).info(
    "Carbon is a code snippet sharing service. You can make carbon of your code and share it with others."
).done()

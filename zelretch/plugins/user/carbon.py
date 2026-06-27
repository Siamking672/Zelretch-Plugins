import asyncio
import os

from kurigram.types import Message

from zelretch.functions.driver import Driver

from . import HelpMenu, zelretch, on_message


@on_message("carbon", allow_master=True)
async def carbon(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me some code to make carbon.")

    code = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "**[ 50% ]** __Making carbon...__")

    driver, resp = Driver.get()
    if not driver:
        return await zelretch.error(message, resp)

    await kaleido.edit("**[ 75% ]** __Making carbon...__")
    image = await Driver.generate_carbon(driver, code)
    await asyncio.sleep(4)

    await kaleido.edit("**[ 100% ]** __Uploading carbon...__")
    Driver.close(driver)

    await kaleido.reply_photo(image, caption=f"**𝖢𝖺𝗋𝖻𝗈𝗇𝖾𝖽:**\n`{code}`")
    await kaleido.delete()
    os.remove(image)


@on_message("karbon", allow_master=True)
async def karbon(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me some code to make karbon.")

    code = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "**[ 50% ]** __Making karbon...__")

    driver, resp = Driver.get()
    if not driver:
        return await zelretch.error(message, resp)

    await kaleido.edit("**[ 75% ]** __Making karbon...__")
    image = await Driver.generate_carbon(driver, code, True)
    await asyncio.sleep(4)

    await kaleido.edit("**[ 100% ]** __Uploading karbon...__")
    Driver.close(driver)

    await kaleido.reply_photo(image, caption=f"**𝖢𝖺𝗋𝖻𝗈𝗇𝖾𝖽:**\n`{code}`")
    await kaleido.delete()
    os.remove(image)


HelpMenu("carbon").add(
    "carbon",
    "<code snippet>",
    "Generate a carbon.now.sh image of the given code snippet using a fixed default theme.",
    "carbon print('Hello World!')",
    "The theme is fixed for consistency across snippets.",
).add(
    "karbon",
    "<code snippet>",
    "Generate a carbon.now.sh image of the given code snippet using a randomly chosen theme each time.",
    "karbon print('Hello World!')",
    "Use this command for variety; the theme changes on every invocation.",
).info(
    "Render code snippets as shareable carbon.now.sh images without leaving Telegram."
).done()

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

from zelretch.core import LOGS
from zelretch.functions.runtime import restart

from ..btnsG import gen_bot_help_buttons, start_button
from . import HELP_MSG, START_MSG, BotHelp, Config, zelretch


@zelretch.bot.on_message(filters.command("start") & Config.AUTH_USERS)
async def start_pm(_, message: Message):
    btns = start_button()

    await message.reply_text(
        START_MSG.format(message.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(btns),
    )


@zelretch.bot.on_message(filters.command("help") & Config.AUTH_USERS)
async def help_pm(_, message: Message):
    btns = await gen_bot_help_buttons()

    await message.reply_text(
        HELP_MSG,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(btns),
    )


@zelretch.bot.on_message(filters.command("restart") & Config.AUTH_USERS)
async def restart_clients(_, message: Message):
    await message.reply_text("**🔴 Restarting Zelretch. Reopening the Kaleidoscope...**")
    try:
        await restart()
    except Exception as e:
        LOGS.error(e)
        await message.reply_text(f"**Restart failed:** `{e}`")


BotHelp("Others").add(
    "start", "To start the bot and get the main menu."
).add(
    "help", "To get the help menu with all commands for this assistant bot."
).add(
    "restart", "To restart the bot."
).info(
    "Basic bot commands."
).done()

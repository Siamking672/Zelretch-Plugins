import os

import requests
from bs4 import BeautifulSoup
from kurigram import Client, filters
from kurigram.types import Message

from zelretch import LOGS

from . import (
    Config,
    HelpMenu,
    Symbols,
    custom_handler,
    db,
    group_only,
    handler,
    zelretch,
    on_message,
)


@on_message("addgatcha", chat_type=group_only, allow_master=True)
async def addgatcha(client: Client, message: Message):
    if len(message.command) < 3:
        return await zelretch.delete(
            message, f"For detailed guide check `{handler}help waifu`"
        )

    try:
        bot = await client.get_users(message.command[1])
    except Exception as e:
        return await zelretch.error(message, str(e))

    if not bot:
        return await zelretch.delete(message, "Bot not found!")
    if not bot.is_bot:
        return await zelretch.delete(message, "This is not a bot!")

    catch_command = message.command[2]
    chat_id = message.chat.id
    if len(message.command) > 3 and message.command[3].lower() == "-g":
        chat_id = 0

    await db.add_gachabot(client.me.id, (bot.id, bot.username), catch_command, chat_id)
    await zelretch.delete(
        message,
        f"**Added {bot.username} to gatcha bots list.**\n\n"
        f"**{Symbols.anchor} Catch command:** `{catch_command}`\n"
        f"**{Symbols.anchor} Chat:** `{'All groups' if chat_id == 0 else message.chat.title}`",
        30,
    )
    if bot.id not in Config.GACHA_BOTS:
        Config.GACHA_BOTS.add(bot.id)


@on_message("delgatcha", chat_type=group_only, allow_master=True)
async def delgatcha(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(
            message, f"For detailed guide check `{handler}help waifu`"
        )

    try:
        bot = await client.get_users(message.command[1])
    except Exception as e:
        return await zelretch.error(message, str(e))

    if not bot:
        return await zelretch.delete(message, "Bot not found!")

    chat_id = message.chat.id
    if len(message.command) > 2 and message.command[2].lower() == "-g":
        chat_id = 0

    if len(message.command) > 2 and message.command[2].lower() == "-a":
        await db.rm_gachabot(client.me.id, bot.id)
        return await zelretch.delete(
            message, f"**Removed {bot.username} from gatcha bots list for all chats.**"
        )

    if await db.is_gachabot(client.me.id, bot.id, chat_id):
        await db.rm_gachabot(client.me.id, bot.id, chat_id)
        await zelretch.delete(
            message,
            f"**Removed {bot.username} from gatcha bots list from {'All groups' if chat_id == 0 else message.chat.title}.**",
        )
        if bot.id not in await db.get_all_gachabots_id():
            Config.GACHA_BOTS.remove(bot.id)
    else:
        await zelretch.delete(
            message, f"{bot.username} is not in the gatcha bots list for this chat."
        )


@on_message("gatchalist", chat_type=group_only, allow_master=True)
async def gatchalist(client: Client, message: Message):
    kaleido = await zelretch.edit(message, "`Fetching gatcha bot list ...`")
    gatchabots = await db.get_all_gachabots(client.me.id)

    if len(gatchabots) > 0:
        text = f"**🎰 Gatcha Bots List:**\n\n"
        for bot in gatchabots:
            text += f"**{Symbols.diamond_2} @{bot.get('username')} :** `{bot.get('catch_command')}`\n"
        text += f"\n**Total:** `{len(gatchabots)}`"
    else:
        text = "No gatcha bots found in the list."

    await kaleido.edit(text, disable_web_page_preview=True)


@on_message("gatcha", chat_type=group_only, allow_master=True)
async def gatchainfo(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(
            message, f"For detailed guide check `{handler}help waifu`"
        )

    try:
        bot = await client.get_users(message.command[1])
    except Exception as e:
        return await zelretch.error(message, str(e))

    chat_id = message.chat.id
    if len(message.command) > 2 and message.command[2].lower() == "-g":
        chat_id = 0

    if await db.is_gachabot(client.me.id, bot.id, chat_id):
        info = await db.get_gachabot(client.me.id, bot.id, chat_id)
        text = (
            f"**🎰 Gatcha Bot Info:**\n\n"
            f"**{Symbols.diamond_2} Bot:** @{bot.username}\n"
            f"**{Symbols.diamond_2} Catch Command:** `{info.get('catch_command')}`\n"
            f"**{Symbols.diamond_2} Chat:** `{'All groups' if info.get('chat_id') == 0 else message.chat.title}`\n"
            f"**{Symbols.diamond_2} Added On:** `{info.get('date')}`"
        )
        return await zelretch.edit(message, text)

    await zelretch.delete(message, "Bot not found in the gatcha bots list.")


@custom_handler(Config.GACHA_BOTS & filters.photo & filters.group & filters.incoming)
async def gacha_handler(client: Client, message: Message):
    if message.from_user.id not in Config.GACHA_BOTS:
        return

    info = await db.get_gachabot(client.me.id, message.from_user.id, 0)
    if not info:
        info = await db.get_gachabot(
            client.me.id, message.from_user.id, message.chat.id
        )

    if not info:
        return

    bot_un = "@collect_waifu_cheats_bot"
    if message.caption and info.get("catch_command") in message.caption:
        try:
            await client.unblock_user(bot_un)
            try:
                msg1: Message = await client.ask(bot_un, f"/start", timeout=60)
            except Exception as e:
                return LOGS.error(str(e))
            msg2: Message = await message.forward(bot_un)
            msg3: Message = await client.listen(
                msg1.chat.id, filters=filters.text & filters.user(bot_un), timeout=60
            )
            if "copy-string:" in msg3.text.lower():
                guess = msg3.text.split("Copy-String:")[1].strip()
                await client.send_message(
                    message.chat.id,
                    guess,
                    disable_web_page_preview=True,
                    reply_to_message_id=message.id,
                )
            await msg1.request.delete()
            await msg1.delete()
            await msg2.delete()
            await msg3.delete()
        except Exception as e:
            LOGS.info(str(e))


HelpMenu("gatcha").add(
    "addgatcha",
    "<bot username/id> <catch command> <-g (optional)>",
    "Register a gacha bot so the userbot auto-sends the catch command whenever it spawns a character. Use the -g flag to enable auto-catch in every group the userbot is in, otherwise it only applies to the current chat.",
    "addgatcha @WaifuBot /protecc",
    "The catch command is whatever the bot expects (e.g. /protecc, /catch, /grab).",
).add(
    "delgatcha",
    "<bot username/id> <flag (optional)>",
    "Remove a gacha bot from the auto-catch list. Without a flag, removes it from the current chat only.",
    "delgatcha @WaifuBot",
    "Flags: '-g' removes the bot from all groups; '-a' removes it from every chat.",
).add(
    "gatchalist",
    None,
    "List every gacha bot the userbot is currently auto-catching for, along with its catch command.",
    "gatchalist",
).add(
    "gatcha",
    "<bot username/id>",
    "Show the configuration of a single registered gacha bot, including the catch command and target chats.",
    "gatcha @WaifuBot",
).info(
    "Auto-catcher for gacha bots — automatically runs the catch command when a character spawns."
).done()

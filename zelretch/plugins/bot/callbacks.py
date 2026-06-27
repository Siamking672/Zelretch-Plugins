from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from zelretch.functions.templates import command_template, help_template
from zelretch.functions.runtime import restart

from ..btnsG import gen_bot_help_buttons, gen_inline_help_buttons, start_button
from ..btnsK import session_inline_keyboard
from . import HELP_MSG, START_MSG, Config, Symbols, zelretch


async def check_auth_click(cb: CallbackQuery) -> bool:
    if cb.from_user.id not in Config.AUTH_USERS:
        await cb.answer(
            "Only authorized Bound Masters can enter this workshop.\n\n🔴",
            show_alert=True,
        )
        return False
    return True


@zelretch.bot.on_callback_query(filters.regex(r"auth_close"))
async def auth_close_cb(_, cb: CallbackQuery):
    if await check_auth_click(cb):
        await cb.message.delete()


@zelretch.bot.on_callback_query(filters.regex(r"close"))
async def close_cb(_, cb: CallbackQuery):
    await cb.message.delete()


@zelretch.bot.on_callback_query(filters.regex(r"bot_help_menu"))
async def bot_help_menu_cb(_, cb: CallbackQuery):
    if not await check_auth_click(cb):
        return

    plugin = str(cb.data.split(":")[1])

    try:
        buttons = [
            InlineKeyboardButton(i, f"bot_help_cmd:{plugin}:{i}")
            for i in sorted(Config.BOT_HELP[plugin]["commands"])
        ]
    except KeyError:
        await cb.answer("No description provided for this plugin!", show_alert=True)
        return

    buttons = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    buttons.append([InlineKeyboardButton(Symbols.back, "help_data:bothelp")])

    caption = (
        f"**Mystic Code:** `{plugin}`\n"
        f"**Archive Note:** __{Config.BOT_HELP[plugin]['info']} 🍀__\n\n"
        f"**📜 Loaded Spells:** `{len(sorted(Config.BOT_HELP[plugin]['commands']))}`"
    )

    try:
        await cb.edit_message_text(
            caption,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception:
        # handles MessageNotModified error
        pass


@zelretch.bot.on_callback_query(filters.regex(r"bot_help_cmd"))
async def bot_help_cmd_cb(_, cb: CallbackQuery):
    if not await check_auth_click(cb):
        return

    result = ""
    plugin = str(cb.data.split(":")[1])
    command = str(cb.data.split(":")[2])

    if plugin in ("Sessions", "Command Seals") and command == "session":
        await cb.answer()
        await cb.edit_message_text(
            "**🔴 Command Seal Registry**\n\nSummon, sever, or inspect bound userbot contracts.",
            reply_markup=InlineKeyboardMarkup(session_inline_keyboard()),
        )
        return

    # In the bot command archive, these buttons should perform the action,
    # not only show another description page.
    if plugin == "Others" and command == "start":
        await cb.answer()
        await cb.edit_message_text(
            START_MSG.format(cb.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(start_button()),
        )
        return

    if plugin == "Others" and command == "help":
        await cb.answer()
        buttons = await gen_bot_help_buttons()
        await cb.edit_message_text(
            HELP_MSG,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if plugin == "Others" and command == "restart":
        await cb.answer("Restarting Zelretch...")
        await cb.edit_message_text("**🔴 Restarting Zelretch. Reopening the Kaleidoscope...**")
        await restart()
        return

    cmd_dict = Config.BOT_HELP[plugin]["commands"][command]

    result += f"**{Symbols.radio_select} Spell:** `/{cmd_dict['command']}`"
    result += (
        f"\n\n**{Symbols.arrow_right} Effect:** __{cmd_dict['description']}__"
    )
    result += f"\n\n**<\\> 🍀**"

    buttons = [
        [
            InlineKeyboardButton(Symbols.back, f"bot_help_menu:{plugin}"),
            InlineKeyboardButton(Symbols.close, "help_data:botclose"),
        ]
    ]

    try:
        await cb.edit_message_text(
            text=result,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception as e:
        await cb.answer(f"Button error: {e}", show_alert=True)


@zelretch.bot.on_callback_query(filters.regex(r"help_page"))
async def help_page_cb(_, cb: CallbackQuery):
    if not await check_auth_click(cb):
        return

    page = int(cb.data.split(":")[1])
    buttons, max_page = await gen_inline_help_buttons(page, sorted(Config.CMD_MENU))

    caption = await help_template(
        cb.from_user.mention,
        (len(Config.CMD_INFO), len(Config.CMD_MENU)),
        (page + 1, max_page),
    )

    try:
        await cb.edit_message_text(
            caption,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception:
        # handles MessageNotModified error
        pass


@zelretch.bot.on_callback_query(filters.regex(r"help_menu"))
async def help_menu_cb(_, cb: CallbackQuery):
    if not await check_auth_click(cb):
        return

    page = int(cb.data.split(":")[1])
    plugin = str(cb.data.split(":")[2])

    try:
        buttons = [
            InlineKeyboardButton(i, f"help_cmd:{page}:{plugin}:{i}")
            for i in sorted(Config.HELP_DICT[plugin]["commands"])
        ]
    except KeyError:
        await cb.answer("No description provided for this plugin!", show_alert=True)
        return

    buttons = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    buttons.append([InlineKeyboardButton(Symbols.back, f"help_page:{page}")])

    caption = await command_template(
        plugin,
        Config.HELP_DICT[plugin]["info"],
        len(sorted(Config.HELP_DICT[plugin]["commands"])),
    )

    try:
        await cb.edit_message_text(
            caption,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception:
        # handles MessageNotModified error
        pass


@zelretch.bot.on_callback_query(filters.regex(r"help_cmd"))
async def help_cmd_cb(_, cb: CallbackQuery):
    if not await check_auth_click(cb):
        return

    page = int(cb.data.split(":")[1])
    plugin = str(cb.data.split(":")[2])
    command = str(cb.data.split(":")[3])
    result = ""
    cmd_dict = Config.HELP_DICT[plugin]["commands"][command]

    if cmd_dict["parameters"] is None:
        result += f"**{Symbols.radio_select} Spell:** `{Config.HANDLERS[0]}{cmd_dict['command']}`"
    else:
        result += f"**{Symbols.radio_select} Spell:** `{Config.HANDLERS[0]}{cmd_dict['command']} {cmd_dict['parameters']}`"

    if cmd_dict["description"]:
        result += (
            f"\n\n**{Symbols.arrow_right} Effect:** __{cmd_dict['description']}__"
        )

    if cmd_dict["example"]:
        result += f"\n\n**{Symbols.arrow_right} Incantation:** `{Config.HANDLERS[0]}{cmd_dict['example']}`"

    if cmd_dict["note"]:
        result += f"\n\n**{Symbols.arrow_right} 𝖭𝗈𝗍𝖾:** __{cmd_dict['note']}__"

    result += f"\n\n**<\\> 🍀**"

    buttons = [
        [
            InlineKeyboardButton(Symbols.back, f"help_menu:{page}:{plugin}"),
            InlineKeyboardButton(Symbols.close, "help_data:c"),
        ]
    ]

    try:
        await cb.edit_message_text(
            result,
            ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception:
        # handles MessageNotModified error
        pass


@zelretch.bot.on_callback_query(filters.regex(r"help_data"))
async def help_close_cb(_, cb: CallbackQuery):
    if not await check_auth_click(cb):
        return

    action = str(cb.data.split(":")[1])
    if action == "c":
        await cb.edit_message_text(
            "**📕 Grimoire sealed.**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Reopen Grimoire", "help_data:reopen")]]
            ),
        )
    elif action == "reopen":
        buttons, pages = await gen_inline_help_buttons(0, sorted(Config.CMD_MENU))
        caption = await help_template(
            cb.from_user.mention,
            (len(Config.CMD_INFO), len(Config.CMD_MENU)),
            (1, pages),
        )
        await cb.edit_message_text(
            caption,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    elif action == "botclose":
        await cb.message.delete()
    elif action == "bothelp":
        buttons = await gen_bot_help_buttons()
        await cb.edit_message_text(
            HELP_MSG,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    elif action == "source":
        buttons = [
            [
                InlineKeyboardButton("Main Archive", url="https://github.com/Siamking672/Zelretch"),
                InlineKeyboardButton("Mystic Codes", url="https://github.com/Siamking672/Zelretch-Plugins"),
            ],
            [
                InlineKeyboardButton("back", "help_data:start"),
                InlineKeyboardButton(Symbols.close, "help_data:botclose"),
            ],
        ]
        await cb.edit_message_text(
            "__» Zelretch is a Fate-inspired, Rin Tohsaka-themed userbot workshop.__\n"
            "__» The main archive contains the Docker launcher; the Mystic Codes archive contains the plugins.__\n"
            "__» The project is open-source and can be modified for your own private setup.__\n\n"
            "__» Do not buy an unofficial copy from anyone claiming to sell this code.__\n"
            "__» Open the archives below for setup and source details.__\n\n"
            "**❤️ 🇧🇩 🔴**",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    elif action == "start":
        buttons = start_button()
        await cb.edit_message_text(
            START_MSG.format(cb.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)

from ..btnsG import gen_inline_keyboard, start_button
from ..btnsK import session_inline_keyboard, session_keyboard
from . import START_MSG, BotHelp, Config, Symbols, db, zelretch


SESSION_MENU_TEXT = "**🔴 Command Seal Registry**\n\nSummon, sever, or inspect bound userbot contracts."


def _session_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(session_inline_keyboard())


async def _check_auth_callback(cb: CallbackQuery) -> bool:
    if cb.from_user.id not in Config.AUTH_USERS:
        await cb.answer(
            "Only authorized Bound Masters can enter this workshop.",
            show_alert=True,
        )
        return False
    return True


async def _show_session_menu_message(message: Message):
    await message.reply_text(
        SESSION_MENU_TEXT,
        reply_markup=_session_markup(),
    )


async def _show_session_menu_callback(cb: CallbackQuery):
    if not await _check_auth_callback(cb):
        return
    await cb.answer()
    try:
        await cb.edit_message_text(
            SESSION_MENU_TEXT,
            reply_markup=_session_markup(),
        )
    except Exception:
        await cb.message.reply_text(
            SESSION_MENU_TEXT,
            reply_markup=_session_markup(),
        )


@zelretch.bot.on_message(
    filters.command("session") & Config.AUTH_USERS & filters.private
)
async def session_menu(_, message: Message):
    await _show_session_menu_message(message)


@zelretch.bot.on_message(filters.regex(r"^(?:📟 Session|🔴 Command Seals|Command Seals)$") & Config.AUTH_USERS & filters.private)
async def session_keyboard_menu(_, message: Message):
    await _show_session_menu_message(message)


@zelretch.bot.on_callback_query(filters.regex(r"^session:menu$"))
async def session_menu_cb(_, cb: CallbackQuery):
    await _show_session_menu_callback(cb)


async def _create_new_session(message: Message):
    await message.reply_text(
        "**Contract ritual started.** Let's bind a new userbot account to Zelretch.",
        reply_markup=ReplyKeyboardRemove(),
    )

    phone_number = await zelretch.bot.ask(
        message.chat.id,
        "**1. Command Seal: Contact**\nEnter the Telegram account phone number for the new contract.\n\n"
        "Use international format, for example: `+8801XXXXXXXXX`\n\n"
        "Send /cancel to stop this ritual.",
        filters=filters.text,
        timeout=120,
    )

    if phone_number.text == "/cancel":
        return await message.reply_text("**Ritual cancelled.**")

    phone_text = phone_number.text.strip()
    if not phone_text.startswith("+") or not phone_text[1:].isdigit():
        return await message.reply_text(
            "**Ritual error.** Phone number must include country code and digits only.\n"
            "Example: `+8801XXXXXXXXX`"
        )

    client = None
    try:
        client = Client(
            name="ZelretchContract",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            in_memory=True,
        )
        await client.connect()

        code = await client.send_code(phone_text)
        ask_otp = await zelretch.bot.ask(
            message.chat.id,
            "**2. Command Seal: Code**\nEnter the OTP sent by Telegram.\n\n"
            "Separate every digit with a space.\n"
            "Example: `2 4 1 7 4`\n\n"
            "Send /cancel to stop this ritual.",
            filters=filters.text,
            timeout=300,
        )
        if ask_otp.text == "/cancel":
            return await message.reply_text("**Ritual cancelled.**")
        otp = ask_otp.text.replace(" ", "")

        try:
            await client.sign_in(phone_text, code.phone_code_hash, otp)
        except SessionPasswordNeeded:
            two_step_pass = await zelretch.bot.ask(
                message.chat.id,
                "**3. Command Seal: Password**\nEnter your two-step verification password.\n\n"
                "Send /cancel to stop this ritual.",
                filters=filters.text,
                timeout=120,
            )
            if two_step_pass.text == "/cancel":
                return await message.reply_text("**Ritual cancelled.**")
            await client.check_password(two_step_pass.text)

        session_string = await client.export_session_string()
        await message.reply_text(
            "**Contract formed.** Session string generated. Sealing it inside the database..."
        )
        user_id = (await client.get_me()).id
        await db.update_session(user_id, session_string)
        await message.reply_text(
            "**Contract sealed.** Session added to the database. Restart Zelretch to summon this account.\n\n"
            "**Security note:** the session string is stored internally and will not be shown in chat."
        )
    except TimeoutError:
        await message.reply_text(
            "**Ritual timeout.** You took too long to complete the contract. Please try again."
        )
    except Exception as e:
        await message.reply_text(f"**Ritual error.** `{e}`")
    finally:
        if client is not None:
            try:
                await client.disconnect()
            except Exception:
                pass


@zelretch.bot.on_message(filters.regex(r"^(?:New 💫|Summon 💎|Summon)$") & Config.AUTH_USERS & filters.private)
async def new_session(_, message: Message):
    await _create_new_session(message)


@zelretch.bot.on_callback_query(filters.regex(r"^session:new$"))
async def new_session_cb(_, cb: CallbackQuery):
    if not await _check_auth_callback(cb):
        return
    await cb.answer()
    await _create_new_session(cb.message)


async def _send_delete_session(message: Message, *, edit: bool = False):
    all_sessions = await db.get_all_sessions()
    if not all_sessions:
        text = "No bound contracts found in the database."
        if edit:
            return await message.edit_text(text, reply_markup=_session_markup())
        return await message.reply_text(text)

    collection = []
    for item in all_sessions:
        collection.append((str(item["user_id"]), f"rm_session:{item['user_id']}"))

    buttons = gen_inline_keyboard(collection, 2)
    buttons.append([InlineKeyboardButton("Back", "session:menu")])
    buttons.append([InlineKeyboardButton("Cancel", "auth_close")])

    text = "**Choose a contract to sever:**"
    if edit:
        return await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    return await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@zelretch.bot.on_message(
    filters.regex(r"^(?:Delete ❌|Sever 🗡️|Sever)$") & Config.AUTH_USERS & filters.private
)
async def delete_session(_, message: Message):
    await _send_delete_session(message)


@zelretch.bot.on_callback_query(filters.regex(r"^session:delete$"))
async def delete_session_cb(_, cb: CallbackQuery):
    if not await _check_auth_callback(cb):
        return
    await cb.answer()
    await _send_delete_session(cb.message, edit=True)


@zelretch.bot.on_callback_query(filters.regex(r"^rm_session:"))
async def rm_session_cb(client: Client, cb: CallbackQuery):
    if not await _check_auth_callback(cb):
        return

    user_id = int(cb.data.split(":", 1)[1])
    all_sessions = await db.get_all_sessions()

    if not all_sessions:
        return await cb.message.delete()

    try:
        owner = await client.get_users(Config.OWNER_ID)
        owner_id = owner.id
        owner_name = owner.first_name
    except Exception:
        owner_id = Config.OWNER_ID
        owner_name = "Owner"

    if cb.from_user.id not in [user_id, owner_id]:
        return await cb.answer(
            f"Access restricted. Only {owner_name} and the contract owner can sever this session.",
            show_alert=True,
        )

    await db.rm_session(user_id)
    await cb.answer("Contract severed. Restart Zelretch to apply changes.", show_alert=True)

    remaining_sessions = [item for item in all_sessions if item["user_id"] != user_id]
    if not remaining_sessions:
        return await cb.message.edit_text(
            "No bound contracts found in the database.",
            reply_markup=_session_markup(),
        )

    collection = []
    for item in remaining_sessions:
        collection.append((str(item["user_id"]), f"rm_session:{item['user_id']}"))

    buttons = gen_inline_keyboard(collection, 2)
    buttons.append([InlineKeyboardButton("Back", "session:menu")])
    buttons.append([InlineKeyboardButton("Cancel", "auth_close")])

    await cb.message.edit_reply_markup(InlineKeyboardMarkup(buttons))


async def _send_session_list(message: Message, *, edit: bool = False):
    all_sessions = await db.get_all_sessions()
    if not all_sessions:
        text = "No bound contracts found in the database."
        if edit:
            return await message.edit_text(text, reply_markup=_session_markup())
        return await message.reply_text(text)

    text = f"**{Symbols.cross_mark} Master Contract Roster**\n\n"
    for i, session in enumerate(all_sessions, start=1):
        text += f"[{i:02d}] {Symbols.bullet} **Master ID:** `{session['user_id']}`\n"

    buttons = [[InlineKeyboardButton("Back", "session:menu")]]
    if edit:
        return await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    return await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@zelretch.bot.on_message(filters.regex(r"^(?:List 📜|Roster 📜|Roster)$") & Config.AUTH_USERS & filters.private)
async def list_sessions(_, message: Message):
    await _send_session_list(message)


@zelretch.bot.on_callback_query(filters.regex(r"^session:list$"))
async def list_sessions_cb(_, cb: CallbackQuery):
    if not await _check_auth_callback(cb):
        return
    await cb.answer()
    await _send_session_list(cb.message, edit=True)


@zelretch.bot.on_message(filters.regex(r"^(?:Home 🏠|Workshop 🏠|Workshop)$") & filters.private & Config.AUTH_USERS)
async def go_home(_, message: Message):
    await message.reply_text(
        "**Workshop**",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.reply_text(
        START_MSG.format(message.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(start_button()),
    )


@zelretch.bot.on_callback_query(filters.regex(r"^session:home$"))
async def session_home_cb(_, cb: CallbackQuery):
    if not await _check_auth_callback(cb):
        return
    await cb.answer()
    await cb.edit_message_text(
        START_MSG.format(cb.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(start_button()),
    )


BotHelp("Command Seals").add(
    "session", "Open the Command Seal registry to summon, sever, or list userbot contracts."
).info(
    "Command Seal Registry"
).done()

"""
.session — interactive in-bot userbot session creation.

For users who skipped session creation in the setup wizard (and started
the bot in BOT_TOKEN-only / assistant-bot mode), this command walks them
through the same flow interactively inside Telegram:

  1. User DMs the bot: .session
  2. Bot asks for phone number → user replies
  3. Bot sends code request → asks user for the login code
  4. (If 2FA enabled) Bot asks for the cloud password → user replies
  5. Bot generates the session string, saves it to .env (and DB), and
     tells the user to run .restart to enable userbot mode.

The state machine uses a per-user dict so multiple users can run the
flow concurrently (though typically only the owner does this).
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Any

from pyrogram import filters
from pyrogram.errors import (
    PhoneCodeInvalid,
    PhoneCodeExpired,
    PhoneCodeEmpty,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait,
    PhoneNumberInvalid,
)

from astralbot import on_command, on_event, help_menu, Config, db, LOGS


__plugin_name__ = "Session"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Interactively create a userbot session from inside Telegram."
__plugin_category__ = "core"


# Per-user state machine. Maps user_id -> state dict.
# state dict keys:
#   "step": "phone" | "code" | "password"
#   "phone": str
#   "phone_code_hash": str
#   "client": pyrogram.Client  (long-lived during the flow)
#   "started_at": float
_STATES: dict[int, dict[str, Any]] = {}

# Conversation timeout — auto-cancel after 5 minutes of inactivity
_TIMEOUT_SECONDS = 5 * 60


@on_command("session", description="Create a userbot session interactively.", permission="owner")
async def session_cmd(client, message):
    if not message.from_user:
        return
    uid = message.from_user.id
    # Cancel any existing flow for this user
    await _cancel_flow(uid)
    _STATES[uid] = {"step": "phone", "started_at": asyncio.get_event_loop().time()}
    await message.reply_text(
        "🔐 **Session creation wizard**\n\n"
        "Please reply with your phone number (with country code, e.g. `+15551234567`).\n\n"
        "Telegram will send a login code to this number.\n\n"
        "To cancel, send `.cancel`."
    )


@on_command("cancel", description="Cancel the in-progress session creation flow.", permission="owner")
async def cancel_cmd(client, message):
    if not message.from_user:
        return
    uid = message.from_user.id
    if uid in _STATES:
        await _cancel_flow(uid)
        await message.reply_text("✅ Session creation cancelled.")
    else:
        await message.reply_text("ℹ️ No active session creation flow.")


@on_event(filters.incoming & filters.private & filters.text)
async def session_flow_watcher(client, message):
    """Watch for replies during the session creation flow."""
    if not message.from_user or not message.text:
        return
    uid = message.from_user.id
    if uid not in _STATES:
        return
    state = _STATES[uid]

    # Check timeout
    now = asyncio.get_event_loop().time()
    if now - state.get("started_at", now) > _TIMEOUT_SECONDS:
        await _cancel_flow(uid)
        await message.reply_text("⏰ Session creation timed out. Run `.session` to try again.")
        return

    text = message.text.strip()

    # Allow `.cancel` to interrupt
    if text.lower().startswith(f"{Config.primary_prefix}cancel") or text.lower() == "cancel":
        await _cancel_flow(uid)
        await message.reply_text("✅ Cancelled.")
        return

    if state["step"] == "phone":
        await _handle_phone(client, message, state, text)
    elif state["step"] == "code":
        await _handle_code(client, message, state, text)
    elif state["step"] == "password":
        await _handle_password(client, message, state, text)


async def _handle_phone(client, message, state: dict, phone: str) -> None:
    # Basic validation — accept +digits, possibly with spaces
    if not re.match(r"^\+?\d[\d\s\-]+$", phone):
        await message.reply_text("❌ That doesn't look like a phone number. Try again with format `+15551234567`.")
        return
    phone_clean = phone.replace(" ", "").replace("-", "")
    if not phone_clean.startswith("+"):
        phone_clean = "+" + phone_clean

    msg = await message.reply_text("📞 Sending login code...")
    try:
        from pyrogram import Client
        wizard_client = Client(
            name=f"astralbot_session_{message.from_user.id}",
            api_id=Config.api_id,
            api_hash=Config.api_hash,
            in_memory=True,
        )
        await wizard_client.connect()
        sent = await wizard_client.send_code(phone_clean)
        state["phone"] = phone_clean
        state["phone_code_hash"] = sent.phone_code_hash
        state["client"] = wizard_client
        state["step"] = "code"
        state["started_at"] = asyncio.get_event_loop().time()
        await msg.edit_text(
            f"✅ Login code sent to `{phone_clean}`.\n\n"
            "Please reply with the code you received (e.g. `12345`)."
        )
    except PhoneNumberInvalid:
        await msg.edit_text("❌ Invalid phone number. Run `.session` to start over.")
        await _cancel_flow(message.from_user.id)
    except FloodWait as exc:
        await msg.edit_text(f"⏰ Telegram asked to wait {exc.value}s. Try again later.")
        await _cancel_flow(message.from_user.id)
    except Exception as exc:
        await msg.edit_text(f"❌ Failed to send code: `{exc}`")
        await _cancel_flow(message.from_user.id)


async def _handle_code(client, message, state: dict, code: str) -> None:
    code = code.strip().replace(" ", "").replace("-", "")
    if not code.isdigit():
        await message.reply_text("❌ The code should be digits only. Try again.")
        return
    wizard_client = state.get("client")
    if wizard_client is None:
        await message.reply_text("❌ Session lost. Run `.session` to start over.")
        await _cancel_flow(message.from_user.id)
        return

    msg = await message.reply_text("🔍 Verifying code...")
    try:
        await wizard_client.sign_in(state["phone"], state["phone_code_hash"], code)
        # Success — no 2FA
        session_string = await wizard_client.export_session_string()
        await wizard_client.disconnect()
        state["client"] = None
        await _save_session(message, session_string)
        await msg.edit_text(
            "✅ **Session created successfully!**\n\n"
            "The session has been saved to `.env` and to the database.\n"
            "Run `.restart` now to enable userbot mode."
        )
        await _cancel_flow(message.from_user.id)
    except SessionPasswordNeeded:
        state["step"] = "password"
        state["started_at"] = asyncio.get_event_loop().time()
        await msg.edit_text(
            "🔒 Your account has two-factor authentication enabled.\n\n"
            "Please reply with your cloud password."
        )
    except (PhoneCodeInvalid, PhoneCodeExpired, PhoneCodeEmpty) as exc:
        await msg.edit_text(f"❌ Code error: `{exc}`. Run `.session` to start over.")
        await _cancel_flow(message.from_user.id)
    except FloodWait as exc:
        await msg.edit_text(f"⏰ Telegram asked to wait {exc.value}s.")
        await _cancel_flow(message.from_user.id)
    except Exception as exc:
        await msg.edit_text(f"❌ Sign-in failed: `{exc}`")
        await _cancel_flow(message.from_user.id)


async def _handle_password(client, message, state: dict, password: str) -> None:
    wizard_client = state.get("client")
    if wizard_client is None:
        await message.reply_text("❌ Session lost. Run `.session` to start over.")
        await _cancel_flow(message.from_user.id)
        return

    msg = await message.reply_text("🔍 Verifying password...")
    try:
        await wizard_client.check_password(password)
        session_string = await wizard_client.export_session_string()
        await wizard_client.disconnect()
        state["client"] = None
        await _save_session(message, session_string)
        await msg.edit_text(
            "✅ **Session created successfully!**\n\n"
            "The session has been saved to `.env` and to the database.\n"
            "Run `.restart` now to enable userbot mode."
        )
        await _cancel_flow(message.from_user.id)
    except PasswordHashInvalid:
        await msg.edit_text("❌ Wrong password. Try again — reply with your cloud password.")
    except FloodWait as exc:
        await msg.edit_text(f"⏰ Telegram asked to wait {exc.value}s.")
        await _cancel_flow(message.from_user.id)
    except Exception as exc:
        await msg.edit_text(f"❌ 2FA failed: `{exc}`")
        await _cancel_flow(message.from_user.id)


async def _save_session(message, session_string: str) -> None:
    """Persist the new session string to .env and the database."""
    # 1. Save to DB
    try:
        await db.insert("sessions", {
            "_id": f"primary:{message.from_user.id}",
            "user_id": message.from_user.id,
            "session": session_string,
            "created_at": asyncio.get_event_loop().time(),
        })
    except Exception as exc:
        LOGS.warning("Failed to save session to DB: %s", exc)

    # 2. Update .env file
    try:
        env_path = Path(os.environ.get("DOTENV_PATH", ".env"))
        if not env_path.exists():
            env_path.write_text(f"STRING_SESSION={session_string}\n", encoding="utf-8")
        else:
            content = env_path.read_text(encoding="utf-8")
            # Replace existing STRING_SESSION line or add a new one
            new_line = f"STRING_SESSION={session_string}"
            lines = content.splitlines()
            found = False
            for i, line in enumerate(lines):
                if line.strip().startswith("STRING_SESSION="):
                    lines[i] = new_line
                    found = True
                    break
            if not found:
                lines.append(new_line)
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        LOGS.info("Session saved to %s", env_path)
    except Exception as exc:
        LOGS.warning("Failed to update .env: %s", exc)


async def _cancel_flow(uid: int) -> None:
    state = _STATES.pop(uid, None)
    if state and state.get("client"):
        try:
            await state["client"].disconnect()
        except Exception:
            pass


help_menu.add(
    command="session",
    description="Interactively create a userbot session (for users who skipped the wizard).",
    example=".session",
    category="core",
    plugin="session",
).register()

help_menu.add(
    command="cancel",
    description="Cancel an in-progress session creation flow.",
    example=".cancel",
    category="core",
    plugin="session",
).register()

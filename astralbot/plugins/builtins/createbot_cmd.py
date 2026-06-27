"""
.createbot — interactively create a new assistant bot via @BotFather.

If the user doesn't have a BOT_TOKEN, this command automates the @BotFather
conversation:

  1. User sends .createbot
  2. Bot asks for a bot name (display name, e.g. "My AstralBot")
  3. User replies → bot sends /newbot to @BotFather, then the name
  4. BotFather asks for a username → bot relays the question
  5. User replies with a username (must end in "bot", e.g. "my_astralbot")
  6. Bot sends the username to BotFather
  7. BotFather sends the bot token → bot extracts it and saves to .env
  8. Bot tells the user to run .restart to start the assistant bot

This only works from the userbot account (not the assistant bot itself).
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

from pyrogram import filters

from astralbot import on_command, on_event, help_menu, Config, LOGS


__plugin_name__ = "Create Bot"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Interactively create a new assistant bot via @BotFather."
__plugin_category__ = "core"


BOTFATHER_USERNAME = "BotFather"
_CREATEBOT_STATES: dict[int, dict] = {}
_TIMEOUT_SECONDS = 5 * 60


@on_command("createbot", description="Create a new assistant bot via @BotFather.", permission="owner")
async def createbot_cmd(client, message):
    if not message.from_user:
        return

    # Check if a BOT_TOKEN is already set
    if Config.bot_token:
        return await message.reply_text(
            "ℹ️ An assistant bot is already configured.\n"
            "To replace it, run `.setvar BOT_TOKEN <new_token>` and `.restart`."
        )

    uid = message.from_user.id
    _CREATEBOT_STATES[uid] = {
        "step": "name",
        "started_at": asyncio.get_event_loop().time(),
    }

    await message.reply_text(
        "🤖 **Create a new assistant bot**\n\n"
        "I'll walk you through creating a new bot via @BotFather.\n\n"
        "**Step 1:** Reply with a **name** for your bot.\n"
        "This is the display name (e.g. `My AstralBot`).\n\n"
        "To cancel, send `.cancel`."
    )


@on_event(filters.incoming & filters.private & filters.text)
async def createbot_flow_watcher(client, message):
    """Watch for replies during the .createbot flow."""
    if not message.from_user or not message.text:
        return
    uid = message.from_user.id
    if uid not in _CREATEBOT_STATES:
        return

    state = _CREATEBOT_STATES[uid]

    # Check timeout
    now = asyncio.get_event_loop().time()
    if now - state.get("started_at", now) > _TIMEOUT_SECONDS:
        _CREATEBOT_STATES.pop(uid, None)
        await message.reply_text("⏰ Bot creation timed out. Run `.createbot` to try again.")
        return

    text = message.text.strip()

    # Allow .cancel to interrupt
    if text.lower().startswith(f"{Config.primary_prefix}cancel") or text.lower() == "cancel":
        _CREATEBOT_STATES.pop(uid, None)
        await message.reply_text("✅ Bot creation cancelled.")
        return

    if state["step"] == "name":
        await _handle_name(client, message, state, text)
    elif state["step"] == "username":
        await _handle_username(client, message, state, text)


async def _handle_name(client, message, state: dict, name: str) -> None:
    if len(name) > 64:
        await message.reply_text("❌ Name too long (max 64 chars). Try again.")
        return

    state["name"] = name
    state["step"] = "username"
    state["started_at"] = asyncio.get_event_loop().time()

    msg = await message.reply_text(f"📝 Sending name `{name}` to @BotFather...")

    try:
        # Start the /newbot conversation with BotFather
        await client.send_message(BOTFATHER_USERNAME, "/newbot")
        await asyncio.sleep(1)
        # Send the bot name
        await client.send_message(BOTFATHER_USERNAME, name)

        # Wait for BotFather's response asking for a username
        botfather_reply = await _wait_for_botfather_reply(client, timeout=15)

        if botfather_reply and ("username" in botfather_reply.lower() or "Username" in botfather_reply):
            await msg.edit_text(
                f"✅ Name accepted: `{name}`\n\n"
                "**Step 2:** Reply with a **username** for your bot.\n"
                "Must end in `bot` and contain only letters, numbers, underscores.\n"
                "Example: `my_astralbot`"
            )
        else:
            # BotFather might have rejected the name or sent an unexpected response
            await msg.edit_text(
                f"⚠️ BotFather response: {botfather_reply or '(no response)'}\n\n"
                "Try a different name. Run `.createbot` to start over."
            )
            _CREATEBOT_STATES.pop(message.from_user.id, None)
    except Exception as exc:
        await msg.edit_text(f"❌ Failed to communicate with @BotFather: `{exc}`")
        _CREATEBOT_STATES.pop(message.from_user.id, None)


async def _handle_username(client, message, state: dict, username: str) -> None:
    username = username.lstrip("@")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]{3,30}bot$", username):
        await message.reply_text(
            "❌ Invalid username. Must:\n"
            "  • Start with a letter\n"
            "  • Be 5-32 chars\n"
            "  • End with `bot`\n"
            "  • Only letters, numbers, underscores\n\n"
            "Try again:"
        )
        return

    state["username"] = username
    msg = await message.reply_text(f"📝 Sending username `@{username}` to @BotFather...")

    try:
        await client.send_message(BOTFATHER_USERNAME, username)

        # Wait for BotFather to send the token (or an error)
        reply = await _wait_for_botfather_reply(client, timeout=20)

        if not reply:
            await msg.edit_text("❌ @BotFather didn't respond. Try `.createbot` again.")
            _CREATEBOT_STATES.pop(message.from_user.id, None)
            return

        # Extract the token from BotFather's response
        # BotFather's message looks like:
        # "Done! Congratulations on your new bot. You will find it at t.me/xxx.
        #  Use this token to access the HTTP API:
        #  123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
        #  ..."
        token_match = re.search(r"(\d{8,}:[A-Za-z0-9_-]{30,})", reply)

        if token_match:
            token = token_match.group(1)
            await _save_bot_token(message, token, state.get("name", "AstralBot"))
            await msg.edit_text(
                f"✅ **Bot created successfully!**\n\n"
                f"Name: `{state.get('name', '?')}`\n"
                f"Username: `@{username}`\n"
                f"Token: `{token[:15]}...` (saved to .env)\n\n"
                f"Run `.restart` now to start the assistant bot."
            )
        elif "taken" in reply.lower() or "already" in reply.lower():
            await msg.edit_text(
                f"❌ Username `@{username}` is already taken.\n"
                f"BotFather says: {reply[:200]}\n\n"
                f"Try a different username. Run `.createbot` again."
            )
        else:
            await msg.edit_text(
                f"⚠️ BotFather response:\n{reply[:300]}\n\n"
                f"If you didn't get a token, try `.createbot` again with a different name/username."
            )
    except Exception as exc:
        await msg.edit_text(f"❌ Failed: `{exc}`")

    _CREATEBOT_STATES.pop(message.from_user.id, None)


async def _wait_for_botfather_reply(client, timeout: int = 15) -> str | None:
    """Wait for a reply from @BotFather. Returns the text of the latest message."""
    try:
        await asyncio.sleep(2)
        async for msg in client.get_chat_history(BOTFATHER_USERNAME, limit=1):
            if msg.text:
                return msg.text
    except Exception as exc:
        LOGS.debug("Error reading BotFather reply: %s", exc)
    return None


async def _save_bot_token(message, token: str, bot_name: str) -> None:
    """Save the BOT_TOKEN to .env and update Config."""
    # Update Config in-memory
    Config.bot_token = token

    # Persist to .env
    try:
        env_path = Path(os.environ.get("DOTENV_PATH", ".env"))
        if not env_path.exists():
            env_path.write_text(f"BOT_TOKEN={token}\n", encoding="utf-8")
        else:
            content = env_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            found = False
            for i, line in enumerate(lines):
                if line.strip().startswith("BOT_TOKEN="):
                    lines[i] = f"BOT_TOKEN={token}"
                    found = True
                    break
            if not found:
                lines.append(f"BOT_TOKEN={token}")
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        LOGS.info("BOT_TOKEN saved to %s", env_path)
    except Exception as exc:
        LOGS.warning("Failed to persist BOT_TOKEN to .env: %s", exc)


help_menu.add(
    command="createbot",
    description="Create a new assistant bot via @BotFather (interactive).",
    example=".createbot",
    category="core",
    plugin="createbot",
).register()

"""
Pyrogram client setup and CustomMethods mixin.

Combines the best of both source projects:
- Multi-account assistant support (Zelretch) via DB-stored session strings
- Primary account from STRING_SESSION env var
- Optional assistant bot account via BOT_TOKEN
- CustomMethods mixin with the convenience helpers used across plugins
  (edit, delete, reply, send_document, check_and_log, etc.)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

from pyrogram import Client
from pyrogram.types import Message

if TYPE_CHECKING:
    from astralbot.core.config import Config
    from astralbot.core.database import Database

LOGS = logging.getLogger("astralbot.client")


class CustomMethods:
    """Shared convenience methods mixed into every Pyrogram client.

    Plugins can call ``await client.edit(message, text)``,
    ``await client.delete(message, text)``, etc.
    """

    async def edit(self, message: Message, text: str, **kwargs: Any) -> Message:
        """Edit a message; gracefully create a new one if it can't be edited."""
        try:
            return await message.edit_text(text, **kwargs)
        except Exception:
            return await message.reply_text(text, **kwargs)

    async def delete(self, message: Message, notice: str | None = None, delay: int = 5) -> Message | None:
        """Edit a message to a notice, wait, then delete it. Return the edited msg."""
        if notice:
            try:
                edited = await message.edit_text(notice)
            except Exception:
                edited = await message.reply_text(notice)
            await asyncio.sleep(delay)
            try:
                await edited.delete()
            except Exception:
                pass
            return edited
        try:
            await message.delete()
        except Exception:
            pass
        return None

    async def check_and_log(self, action: str, text: str, count: int = 0) -> None:
        """Send a summary to LOG_CHAT_ID if configured.

        Mirrors Zelretch's check_and_log — useful for broadcast / gcast / mass
        actions where the user wants a follow-up report in their log channel.
        """
        from astralbot import Config, client as _primary
        if not Config or not Config.log_chat_id or not _primary:
            return
        try:
            summary = f"**{action}** | {text}"
            if count:
                summary += f"\nAffected: `{count}`"
            await _primary.send_message(Config.log_chat_id, summary)
        except Exception:
            pass

    async def safe_send(self, chat_id: int | str, text: str, **kwargs: Any) -> Message | None:
        """Best-effort send — never raises."""
        try:
            return await self.send_message(chat_id, text, **kwargs)
        except Exception as exc:
            LOGS.debug("safe_send failed: %s", exc)
            return None

    async def progress_callback(self, current: int, total: int, status_msg: Message | None = None, label: str = "Progress") -> None:
        """Progress callback for downloads / uploads. Throttled to 1 update/sec."""
        if status_msg is None:
            return
        # Throttle to once per second
        now = time.time()
        if not hasattr(status_msg, "_last_progress") or now - status_msg._last_progress > 1:  # type: ignore[attr-defined]
            status_msg._last_progress = now  # type: ignore[attr-defined]
            pct = (current * 100) / total if total else 0
            bar_len = 20
            filled = int(bar_len * current // total) if total else 0
            bar = "█" * filled + "░" * (bar_len - filled)
            try:
                await status_msg.edit_text(
                    f"{label}\n`{bar}` `{pct:.1f}%` ({current}/{total})"
                )
            except Exception:
                pass


class AstralClient(CustomMethods, Client):
    """Pyrogram Client with AstralBot's CustomMethods mixed in."""

    # Class-level cache: maps client name -> bot user ID (for assistant bots)
    # Set during build_clients so ensure_log_channel / ensure_database_channel
    # can find the assistant bot without calling get_me() again.
    _bot_user_ids: dict[str, int] = {}

    pass


def _find_assistant_bot(clients: list[Client]) -> "AstralClient | None":
    """Find the assistant bot client in the clients list.

    Checks the cached bot user IDs first (populated during build_clients),
    then falls back to checking each client's name attribute.
    """
    # Check the cache first
    for name, uid in AstralClient._bot_user_ids.items():
        for c in clients:
            if getattr(c, "name", None) == name:
                return c  # type: ignore[return-value]
    # Fallback: look for a client named "astralbot_assistant_bot"
    for c in clients:
        if getattr(c, "name", None) == "astralbot_assistant_bot":
            return c  # type: ignore[return-value]
    return None


async def build_clients(config: "Config", db: "Database" | None = None) -> list[Client]:
    """Build the primary client + optional assistant bot + any DB-stored sessions.

    Returns a list of clients. The first element is the "primary" — either the
    userbot account (if STRING_SESSION is set) or the assistant bot (if only
    BOT_TOKEN is set, used in wizard-skipped-session mode).
    """
    clients: list[Client] = []

    # 1. Primary userbot account (if STRING_SESSION is configured)
    if config.string_session:
        primary = AstralClient(
            name="astralbot_primary",
            api_id=config.api_id,
            api_hash=config.api_hash,
            session_string=config.string_session,
            workers=config.workers,
            in_memory=True,
            no_updates=False,
        )
        await primary.start()
        me = await primary.get_me()
        if config.owner_id is None:
            config.owner_id = me.id
            LOGS.info("OWNER_ID auto-detected: %s", config.owner_id)
        LOGS.info("Primary userbot client started: @%s (%s)", me.username, me.id)
        clients.append(primary)
    else:
        LOGS.warning(
            "STRING_SESSION not set — running in assistant-bot-only mode. "
            "Use the `.session` command to create a userbot session later."
        )

    # 2. Optional assistant bot account
    if config.bot_token:
        try:
            bot = AstralClient(
                name="astralbot_assistant_bot",
                api_id=config.api_id,
                api_hash=config.api_hash,
                bot_token=config.bot_token,
                workers=config.workers,
                in_memory=True,
            )
            await bot.start()
            bot_me = await bot.get_me()
            LOGS.info("Assistant bot started: @%s (id=%s, is_bot=%s)", bot_me.username, bot_me.id, getattr(bot_me, "is_bot", "?"))
            # Cache the bot's user ID so ensure_log_channel / ensure_database_channel
            # can find and promote it without calling get_me() again.
            AstralClient._bot_user_ids["astralbot_assistant_bot"] = bot_me.id
            clients.append(bot)
        except Exception as exc:
            LOGS.warning("Failed to start assistant bot: %s", exc)

    # 3. DB-stored additional sessions (multi-account support, Zelretch-style)
    # Skip if db is None (first-pass build before DB is opened)
    if db is not None:
        try:
            sessions = await db.find("sessions")
            for i, sess in enumerate(sessions, start=1):
                try:
                    extra = AstralClient(
                        name=f"astralbot_extra_{i}",
                        api_id=config.api_id,
                        api_hash=config.api_hash,
                        session_string=sess["session"],
                        workers=config.workers,
                        in_memory=True,
                    )
                    await extra.start()
                    extra_me = await extra.get_me()
                    LOGS.info("Extra client #%d started: @%s", i, extra_me.username)
                    clients.append(extra)
                except Exception as exc:
                    LOGS.warning("Failed to start extra session #%d: %s", i, exc)
        except Exception as exc:
            LOGS.debug("No extra sessions to load: %s", exc)

    return clients


async def stop_clients(clients: list[Client]) -> None:
    for c in clients:
        try:
            await c.stop()
        except Exception:
            pass


async def ensure_log_channel(config: "Config", clients: list[Client]) -> int | None:
    """Ensure a LOG_CHAT_ID is configured.

    If ``config.log_chat_id`` is already set, return it as-is.

    If it's not set, use the primary (userbot) client to:
      1. Create a new private channel named "AstralBot Logs"
      2. If an assistant bot is present, add it as an administrator with
         post + edit + delete messages rights.
      3. Save the new channel ID to ``config.log_chat_id`` and persist it
         to ``.env`` (so it survives restarts).

    Returns the LOG_CHAT_ID on success, or None on failure (the bot will
    continue without Telegram log forwarding in that case).
    """
    import logging
    import os
    from pathlib import Path
    from datetime import datetime, timezone

    logs = logging.getLogger("astralbot.client")

    if config.log_chat_id:
        return config.log_chat_id

    if not clients:
        logs.warning("No clients available to create a log channel.")
        return None

    # Use the primary (userbot) client to create the channel — bots can't
    # create channels, only user accounts can.
    primary = clients[0]

    try:
        # Create a new private channel
        # Pyrogram v2 uses create_channel / create_supergroup
        try:
            chat = await primary.create_supergroup(
                title="AstralBot Logs",
                description="Auto-created log channel for AstralBot — WARNING+ logs are forwarded here.",
            )
        except Exception:
            # Fallback: try create_channel
            chat = await primary.create_channel(
                title="AstralBot Logs",
                description="Auto-created log channel for AstralBot — WARNING+ logs are forwarded here.",
            )

        chat_id = chat.id
        # Pyrogram may return the ID without the -100 prefix for supergroups;
        # normalise to the full -100... form that send_message expects.
        if chat_id > 0:
            chat_id = -1000000000000 - chat_id
        # Make sure it has the -100 prefix
        if not str(chat_id).startswith("-100"):
            chat_id = int(f"-100{abs(chat_id)}")

        config.log_chat_id = chat_id
        logs.info("Auto-created log channel: %s (id=%s)", chat.title, chat_id)

        # If there's an assistant bot, add it as admin
        bot_client = _find_assistant_bot(clients)
        if bot_client is not None:
            try:
                bot_me = await bot_client.get_me()
                await primary.promote_chat_member(
                    chat_id,
                    bot_me.id,
                    is_anonymous=False,
                    can_manage_chat=True,
                    can_change_info=True,
                    can_post_messages=True,
                    can_edit_messages=True,
                    can_delete_messages=True,
                    can_invite_users=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_promote_members=False,
                    can_manage_video_chats=False,
                )
                logs.info("Assistant bot @%s (id=%s) promoted to admin in log channel.", bot_me.username, bot_me.id)
            except Exception as exc:
                logs.warning("Failed to promote assistant bot in log channel: %s", exc)
        else:
            logs.info("No assistant bot found — skipping admin promotion in log channel.")

        # Post a welcome message so the user knows what this channel is
        try:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            await primary.send_message(
                chat_id,
                f"📋 **AstralBot Log Channel**\n\n"
                f"This channel was auto-created by AstralBot.\n"
                f"WARNING+ log messages will be forwarded here.\n\n"
                f"Created: `{now}`\n"
                f"Owner: `{config.owner_id}`",
            )
        except Exception:
            pass

        # Persist to .env so it survives restarts
        try:
            env_path = Path(os.environ.get("DOTENV_PATH", ".env"))
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                found = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("LOG_CHAT_ID="):
                        lines[i] = f"LOG_CHAT_ID={chat_id}"
                        found = True
                        break
                if not found:
                    lines.append(f"LOG_CHAT_ID={chat_id}")
                env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                logs.info("LOG_CHAT_ID=%s saved to %s", chat_id, env_path)
        except Exception as exc:
            logs.warning("Failed to persist LOG_CHAT_ID to .env: %s", exc)

        return chat_id

    except Exception as exc:
        logs.warning(
            "Failed to auto-create log channel: %s. "
            "Telegram log forwarding disabled. You can create a channel manually "
            "and set LOG_CHAT_ID via .setvar LOG_CHAT_ID <id>.",
            exc,
        )
        return None


async def ensure_database_channel(config: "Config", clients: list[Client]) -> int | None:
    """Ensure a DATABASE_CHAT_ID is configured for the Telegram channel DB.

    If ``config.database_chat_id`` is already set, or if ``config.database_url``
    is set (MongoDB mode), this is a no-op.

    Otherwise, use the primary (userbot) client to:
      1. Create a new private channel named "AstralBot Database"
      2. If an assistant bot is present, add it as an administrator
      3. Save the new channel ID to ``config.database_chat_id`` and persist
         it to ``.env`` as ``DATABASE_CHAT_ID``.

    Returns the channel ID on success, or None on failure (the bot will fall
    back to SQLite in that case).
    """
    import logging
    import os
    from pathlib import Path
    from datetime import datetime, timezone

    logs = logging.getLogger("astralbot.client")

    # Skip if MongoDB is configured, or if DATABASE_CHAT_ID is already set
    if config.database_url:
        return None
    if config.database_chat_id:
        return config.database_chat_id
    if not clients:
        logs.warning("No clients available to create a database channel.")
        return None

    # Need a userbot account to create a channel
    if not config.string_session:
        logs.info("No userbot session — skipping database channel creation, using SQLite.")
        return None

    primary = clients[0]

    try:
        # Create a new private channel
        try:
            chat = await primary.create_supergroup(
                title="AstralBot Database",
                description="Auto-created database channel for AstralBot — plugin state is stored here as JSON messages.",
            )
        except Exception:
            chat = await primary.create_channel(
                title="AstralBot Database",
                description="Auto-created database channel for AstralBot — plugin state is stored here as JSON messages.",
            )

        chat_id = chat.id
        # Normalise to the full -100... form
        if chat_id > 0:
            chat_id = -1000000000000 - chat_id
        if not str(chat_id).startswith("-100"):
            chat_id = int(f"-100{abs(chat_id)}")

        config.database_chat_id = chat_id
        logs.info("Auto-created database channel: %s (id=%s)", chat.title, chat_id)

        # If there's an assistant bot, add it as admin (so it can read/write too)
        bot_client = _find_assistant_bot(clients)
        if bot_client is not None:
            try:
                bot_me = await bot_client.get_me()
                await primary.promote_chat_member(
                    chat_id,
                    bot_me.id,
                    is_anonymous=False,
                    can_manage_chat=True,
                    can_change_info=True,
                    can_post_messages=True,
                    can_edit_messages=True,
                    can_delete_messages=True,
                    can_invite_users=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_promote_members=False,
                    can_manage_video_chats=False,
                )
                logs.info("Assistant bot @%s (id=%s) promoted to admin in database channel.", bot_me.username, bot_me.id)
            except Exception as exc:
                logs.warning("Failed to promote assistant bot in database channel: %s", exc)
        else:
            logs.info("No assistant bot found — skipping admin promotion in database channel.")

        # Post a welcome message explaining the channel's purpose
        try:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            await primary.send_message(
                chat_id,
                f"🗃️ **AstralBot Database Channel**\n\n"
                f"This channel was auto-created by AstralBot to store plugin state.\n"
                f"Each message here is a JSON document — please don't edit or delete them manually.\n\n"
                f"Created: `{now}`\n"
                f"Owner: `{config.owner_id}`",
            )
        except Exception:
            pass

        # Persist to .env so it survives restarts
        try:
            env_path = Path(os.environ.get("DOTENV_PATH", ".env"))
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                found = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("DATABASE_CHAT_ID="):
                        lines[i] = f"DATABASE_CHAT_ID={chat_id}"
                        found = True
                        break
                if not found:
                    lines.append(f"DATABASE_CHAT_ID={chat_id}")
                env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                logs.info("DATABASE_CHAT_ID=%s saved to %s", chat_id, env_path)
        except Exception as exc:
            logs.warning("Failed to persist DATABASE_CHAT_ID to .env: %s", exc)

        return chat_id

    except Exception as exc:
        logs.warning(
            "Failed to auto-create database channel: %s. "
            "Falling back to SQLite (state will be lost on container restart without persistent storage).",
            exc,
        )
        return None

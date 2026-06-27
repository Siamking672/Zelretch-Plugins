"""Help builtin — renders the command index with inline buttons.

If an assistant bot is available, the help menu is sent as an inline keyboard
with category buttons → command list → command detail, with Back navigation.
If no assistant bot is available, falls back to text (or .txt document for
long output).
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone

from pyrogram import Client
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from astralbot import on_command, help_menu, Config, clients


__plugin_name__ = "Help"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Show available commands with inline button navigation."
__plugin_category__ = "core"

LOGS = logging.getLogger("astralbot.help")

HELP_CB_PREFIX = "astralbot_help:"
_CALLBACKS_REGISTERED = False


# ---------------------------------------------------------------------------
# Keyboard builders
# ---------------------------------------------------------------------------


def _build_category_keyboard() -> InlineKeyboardMarkup:
    """Build the main help menu — category buttons in a 2-column grid."""
    by_cat = help_menu.commands_by_category()
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for cat in sorted(by_cat):
        row.append(InlineKeyboardButton(
            f"{cat.upper()} ({len(by_cat[cat])})",
            callback_data=f"{HELP_CB_PREFIX}cat:{cat}",
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def _build_commands_keyboard(category: str) -> InlineKeyboardMarkup:
    """Build the keyboard for a single category — one button per command + Back."""
    by_cat = help_menu.commands_by_category()
    cmds = by_cat.get(category, [])
    buttons: list[list[InlineKeyboardButton]] = []
    # Show commands in rows of 2
    row: list[InlineKeyboardButton] = []
    for cmd in sorted(cmds, key=lambda c: c.command):
        row.append(InlineKeyboardButton(
            f".{cmd.command}",
            callback_data=f"{HELP_CB_PREFIX}cmd:{cmd.command}",
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("← Back", callback_data=f"{HELP_CB_PREFIX}main")])
    return InlineKeyboardMarkup(buttons)


def _build_cmd_detail_keyboard(category: str) -> InlineKeyboardMarkup:
    """Back button for the command detail view."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"← Back to {category.upper()}", callback_data=f"{HELP_CB_PREFIX}cat:{category}"),
    ]])


# ---------------------------------------------------------------------------
# Text formatters
# ---------------------------------------------------------------------------


def _format_main_text() -> str:
    by_cat = help_menu.commands_by_category()
    lines = ["📋 <b>AstralBot Help</b>", ""]
    lines.append(f"<b>{sum(len(v) for v in by_cat.values())}</b> commands in <b>{len(by_cat)}</b> categories.")
    lines.append("")
    lines.append("Tap a category button below to browse commands.")
    return "\n".join(lines)


def _format_category_text(category: str, prefix: str = ".") -> str:
    by_cat = help_menu.commands_by_category()
    cmds = by_cat.get(category, [])
    lines = [f"📂 <b>{category.upper()}</b> ({len(cmds)} commands)", ""]
    for cmd in sorted(cmds, key=lambda c: c.command):
        args = f" <code>{cmd.args}</code>" if cmd.args else ""
        lines.append(f"<code>{prefix}{cmd.command}</code>{args} — {cmd.description}")
    lines.append("")
    lines.append("Tap a command for details, or ← Back for categories.")
    return "\n".join(lines)


def _format_cmd_detail(command: str, prefix: str = ".") -> str:
    cmd = help_menu.all_commands().get(command)
    if not cmd:
        return f"Command <code>{command}</code> not found."
    text = (
        f"🔧 <b>Command Detail</b>\n\n"
        f"<b>Command:</b> <code>{prefix}{cmd.command}</code>\n"
        f"<b>Plugin:</b> <code>{cmd.plugin}</code>\n"
        f"<b>Category:</b> <code>{cmd.category}</code>\n"
        f"<b>Description:</b> {cmd.description}\n"
    )
    if cmd.args:
        text += f"<b>Args:</b> <code>{cmd.args}</code>\n"
    if cmd.example:
        text += f"<b>Example:</b> <code>{prefix}{cmd.example}</code>\n"
    if cmd.aliases:
        text += f"<b>Aliases:</b> {', '.join('<code>' + a + '</code>' for a in cmd.aliases)}\n"
    if cmd.note:
        text += f"<b>Note:</b> {cmd.note}\n"
    return text


# ---------------------------------------------------------------------------
# Callback handler (registered on the assistant bot)
# ---------------------------------------------------------------------------


async def _help_callback(client: Client, callback: CallbackQuery) -> None:
    """Handle inline button clicks for the help menu."""
    data = callback.data or ""
    if not data.startswith(HELP_CB_PREFIX):
        return

    action = data[len(HELP_CB_PREFIX):]
    prefix = Config.primary_prefix if Config else "."

    try:
        if action == "main":
            await callback.edit_message_text(
                _format_main_text(),
                reply_markup=_build_category_keyboard(),
            )

        elif action.startswith("cat:"):
            category = action[4:]
            await callback.edit_message_text(
                _format_category_text(category, prefix),
                reply_markup=_build_commands_keyboard(category),
            )

        elif action.startswith("cmd:"):
            command = action[4:]
            cmd = help_menu.all_commands().get(command)
            category = cmd.category if cmd else "misc"
            await callback.edit_message_text(
                _format_cmd_detail(command, prefix),
                reply_markup=_build_cmd_detail_keyboard(category),
            )

        await callback.answer()
    except Exception as exc:
        LOGS.debug("Help callback error: %s", exc)
        try:
            await callback.answer("⚠️ Error loading help.", show_alert=True)
        except Exception:
            pass


def _register_callbacks() -> None:
    """Register the help callback handler on the assistant bot (once)."""
    global _CALLBACKS_REGISTERED
    if _CALLBACKS_REGISTERED:
        return
    bot = _find_assistant_bot()
    if bot is not None:
        try:
            bot.add_handler(CallbackQueryHandler(_help_callback))
            _CALLBACKS_REGISTERED = True
            LOGS.info("Help callback handler registered on assistant bot.")
        except Exception as exc:
            LOGS.warning("Failed to register help callback handler: %s", exc)
            _CALLBACKS_REGISTERED = True  # Don't keep trying
    else:
        # No assistant bot available — mark as done so we don't check on every .help call
        _CALLBACKS_REGISTERED = True


def _find_assistant_bot() -> Client | None:
    """Find the assistant bot client in the clients list.

    Uses the shared helper from astralbot.core.client so the detection logic
    is consistent with ensure_log_channel / ensure_database_channel.
    """
    from astralbot import clients
    try:
        from astralbot.core.client import _find_assistant_bot as _find
        return _find(clients or [])
    except Exception:
        # Fallback: check by name
        for c in clients or []:
            if getattr(c, "name", None) == "astralbot_assistant_bot":
                return c
    return None


# ---------------------------------------------------------------------------
# Text fallback helpers
# ---------------------------------------------------------------------------


async def _send_long_text(message: Message, text: str, filename: str = "help.txt", caption: str = "") -> None:
    """Send a long text as a .txt document attachment."""
    buf = io.BytesIO(text.encode("utf-8"))
    buf.name = filename
    try:
        await message.reply_document(
            document=buf,
            caption=caption or None,
            file_name=filename,
        )
    except Exception:
        from astralbot.helpers.formatting import chunk_text
        for chunk in chunk_text(text, max_len=4000):
            try:
                await message.reply_text(chunk)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@on_command(["help", "h"], description="Show all available commands.", permission="sudo")
async def help_cmd(client, message):
    prefix = Config.primary_prefix if Config else "."

    # Try to register callbacks (idempotent)
    _register_callbacks()

    # Find the assistant bot
    bot = _find_assistant_bot()

    if bot:
        # Send inline-button help menu via the assistant bot
        try:
            await bot.send_message(
                message.chat.id,
                _format_main_text(),
                reply_markup=_build_category_keyboard(),
            )
            await message.edit_text("📋 Help menu sent above ↑ (tap a category to browse)")
            return
        except Exception as exc:
            LOGS.debug("Assistant bot couldn't send help to chat %s: %s", message.chat.id, exc)
            # Fall through to text fallback

    # Fallback: text-based help
    text = help_menu.render_help(prefix=prefix)
    if len(text) > 4096:
        await message.edit_text("📋 Help is too long for one message — sending as a document...")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        await _send_long_text(
            message,
            text,
            filename="astralbot-help.txt",
            caption=f"📋 AstralBot command index ({now})",
        )
        return
    await message.edit_text(text)


@on_command("plinfo", description="List loaded plugins with metadata.", permission="sudo")
async def plinfo_cmd(client, message):
    text = help_menu.render_plugin_list()
    if len(text) > 4096:
        await message.edit_text("📋 Plugin list too long — sending as a document...")
        await _send_long_text(
            message,
            text,
            filename="astralbot-plugins.txt",
            caption="📋 AstralBot loaded plugins",
        )
        return
    await message.edit_text(text)


@on_command("cmdinfo", description="Show details for a single command.", permission="sudo")
async def cmdinfo_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}cmdinfo <command>`")
    name = message.command[1].lstrip(Config.primary_prefix)
    text = _format_cmd_detail(name, Config.primary_prefix)
    await message.edit_text(text)

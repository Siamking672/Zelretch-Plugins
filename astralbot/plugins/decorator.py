"""
Decorator-based command and event registration.

The ``@on_command`` decorator is the heart of the plugin API. It:

1. Builds a Pyrogram ``filters.command(cmd, prefixes=Config.handlers)`` filter
   combined with ``filters.me`` (owner) or ``filters.me | filters.user(sudo)``
   when ``allow_sudo=True``.
2. Wraps the function to perform the permission check (owner/sudo/dev/master).
3. Registers the handler on every active client (multi-account support).
4. Tracks the registration so the loader can hot-unload the plugin later.

Inspired by Zelretch's ``@on_message`` decorator (multi-client fan-out +
master-user check) and FoxUserbot's ``fox_command()`` (auto help registration
+ alias support).

Usage::

    from astralbot import on_command, help_menu

    @on_command("ping", description="Pong!")
    async def ping_cmd(client, message):
        await message.edit("🏓 Pong!")

    help_menu.add(
        command="ping",
        args=None,
        description="Check bot latency.",
        example="ping",
        category="core",
        plugin="ping",
    ).register()
"""

from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING, Any, Callable

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

if TYPE_CHECKING:
    from pyrogram import Client

LOGS = logging.getLogger("astralbot.decorator")


# Module-level registries so the loader can hot-unload.
# Map: plugin_name -> list[(client, handler, group)]
_handler_registry: dict[str, list[tuple[Any, MessageHandler, int]]] = {}
# Map: full_module_name -> plugin_name (resolved at load time)
_module_to_plugin: dict[str, str] = {}


# Errors that mean "can't edit this message" — we should fall back to reply
_EDIT_FAILURE_CODES = {
    "MESSAGE_ID_INVALID",
    "MESSAGE_NOT_MODIFIED",
    "MESSAGE_EDIT_TIME_EXPIRED",
    "CHAT_WRITE_FORBIDDEN",
    "MESSAGE_AUTHOR_REQUIRED",
    "PEER_ID_INVALID",
}


def _patch_message_edit(message: Message) -> None:
    """Monkey-patch ``message.edit_text`` so it falls back to ``reply_text``
    on failure.

    This prevents the common ``MESSAGE_ID_INVALID`` error when plugins try to
    edit a message they don't own — e.g.:

      - sudo users issuing commands in groups (the message belongs to the
        sudo user, not the bot account)
      - commands invoked on old messages
      - commands invoked on messages that have been deleted
      - chat write forbidden (banned from chat, restricted, etc.)

    The patch is per-message-instance (it only affects the message object
    passed to the plugin handler), so it doesn't change Pyrogram's global
    behaviour. Plugins can still call ``await message.edit_text(...)`` exactly
    as they did before — they just won't crash on the common failure modes.

    Idempotent: if the message has already been patched, this is a no-op.
    """
    if getattr(message, "_astralbot_edit_patched", False):
        return

    original_edit_text = message.edit_text

    async def safe_edit_text(text: str, *args, **kwargs):
        try:
            return await original_edit_text(text, *args, **kwargs)
        except Exception as exc:
            # Check if the error is one of the "can't edit" codes
            exc_str = str(exc)
            should_fallback = any(code in exc_str for code in _EDIT_FAILURE_CODES)
            if should_fallback:
                # Fall back to reply_text — drop the parse_mode if it's set
                # because reply_text handles it differently
                reply_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k in ("parse_mode", "disable_web_page_preview", "disable_notification", "reply_to_message_id", "quote")
                }
                try:
                    return await message.reply_text(text, *args, **reply_kwargs)
                except Exception:
                    # Last resort: try without any kwargs
                    try:
                        return await message.reply_text(text)
                    except Exception:
                        return message
            # Re-raise non-edit errors (network issues, etc.)
            raise

    message.edit_text = safe_edit_text  # type: ignore[method-assign]
    message._astralbot_edit_patched = True  # type: ignore[attr-defined]


def _current_plugin_name() -> str:
    """Inspect the caller's module and return its registered plugin name.

    Plugin modules are imported with name ``astralbot_plugin_<stem>``;
    we map that to ``<stem>``.
    """
    import sys
    frame = sys._getframe(2)  # skip _current_plugin_name + decorator wrapper
    mod_name = frame.f_globals.get("__name__", "")
    if mod_name.startswith("astralbot_plugin_"):
        return mod_name[len("astralbot_plugin_"):]
    if mod_name.startswith("astralbot.plugins.builtins."):
        return mod_name.rsplit(".", 1)[-1]
    return mod_name.rsplit(".", 1)[-1]


def on_command(
    command: str | list[str],
    *,
    description: str | None = None,
    args: str | None = None,
    example: str | None = None,
    category: str = "misc",
    permission: str = "sudo",
    allow_sudo: bool = True,
    group_only: bool = False,
    private_only: bool = False,
    admin_only: bool = False,
    group: int = 0,
    aliases: list[str] | None = None,
    auto_help: bool = False,
) -> Callable:
    """Register a command handler on every active client.

    Args:
        command: Trigger word (or list of words). Always combined with
                 ``Config.handlers`` prefixes.
        description: Short description (used for auto-help if auto_help=True).
        permission: "owner" | "sudo" | "dev" | "public".
        allow_sudo: If True, sudo/master users may also invoke.
                    (Equivalent to Zelretch's ``allow_master=True``.)
        group_only / private_only: Restrict chat type.
        admin_only: Require caller to be a chat admin.
        group: Pyrogram handler group.
        aliases: Extra trigger words.
        auto_help: If True, auto-register a basic help entry from `description`.
                   Defaults to False — plugins should use `help_menu.add(...).register()`
                   explicitly so they can set args, example, category, plugin.
    """
    def decorator(func: Callable) -> Callable:
        plugin_name = _current_plugin_name()

        @functools.wraps(func)
        async def wrapper(client: "Client", message: Message) -> Any:
            from astralbot import Config, db
            if Config is None or db is None:
                return  # startup not complete yet

            # Make the message object "edit-safe" — patch edit_text to fall
            # back to reply_text on failure. This prevents the common
            # "MESSAGE_ID_INVALID" error when plugins try to edit a message
            # they don't own (e.g. sudo users issuing commands in groups,
            # or commands invoked on old/incoming messages).
            _patch_message_edit(message)

            # Permission check
            user_id = message.from_user.id if message.from_user else (message.sender_chat.id if message.sender_chat else 0)
            is_master = False
            if db is not None:
                try:
                    is_master = await db.is_master(user_id)
                except Exception:
                    is_master = False

            from astralbot.core.permissions import can_run
            if not can_run(permission, user_id, Config, is_master):
                if user_id != 0:
                    try:
                        await message.reply_text("⛔ You don't have permission to use this command.")
                    except Exception:
                        pass
                return

            # Chat type checks
            if group_only and message.chat.type not in ("group", "supergroup"):
                return await message.reply_text("This command only works in groups.")
            if private_only and message.chat.type != "private":
                return await message.reply_text("This command only works in private chat.")
            if admin_only and message.chat.type in ("group", "supergroup"):
                from astralbot.helpers.admin import is_user_admin
                if not await is_user_admin(client, message.chat.id, user_id):
                    return await message.reply_text("⛔ Admins only.")

            # Invoke the handler
            try:
                return await func(client, message)
            except Exception as exc:
                LOGS.exception("Error in command %s: %s", command, exc)
                try:
                    await message.reply_text(f"⚠️ Error: `{exc}`")
                except Exception:
                    pass

        # Build the filter. We use ``filters.me`` by default; for allow_sudo
        # we widen to ``filters.me | filters.user(sudo_list)``. But because
        # the actual sudo set is dynamic (DB masters), we keep the filter permissive
        # at registration time and enforce inside the wrapper.
        from astralbot import Config
        prefixes = Config.handlers if Config else ["."]
        commands = [command] if isinstance(command, str) else list(command)
        if aliases:
            commands.extend(aliases)

        cmd_filter = filters.command(commands, prefixes=prefixes) & ~filters.via_bot
        if allow_sudo:
            cmd_filter = cmd_filter & (filters.me | filters.incoming)
        else:
            cmd_filter = cmd_filter & filters.me

        handler = MessageHandler(wrapper, cmd_filter)

        # Register on every active client
        from astralbot import clients
        registered = []
        for c in clients or []:
            try:
                c.add_handler(handler, group)
                registered.append((c, handler, group))
            except Exception as exc:
                LOGS.warning("Failed to register handler on client: %s", exc)
        _handler_registry.setdefault(plugin_name, []).extend(registered)

        # Auto-register help entry ONLY if auto_help=True. Plugins should
        # use help_menu.add(...).register() explicitly for proper metadata.
        if auto_help and description:
            from astralbot.plugins.help import registry
            registry.add(
                command=command if isinstance(command, str) else command[0],
                args=args,
                description=description,
                example=example or (command if isinstance(command, str) else command[0]),
                category=category,
                plugin=plugin_name,
                aliases=aliases or (command[1:] if isinstance(command, list) else None),
            ).register()

        return wrapper

    return decorator


def on_event(filter_obj, *, group: int = 0) -> Callable:
    """Register a raw Pyrogram filter handler on every active client.

    Used for non-command watchers: AFK auto-reply, antiflood, pmpermit, etc.
    """
    def decorator(func: Callable) -> Callable:
        plugin_name = _current_plugin_name()

        @functools.wraps(func)
        async def wrapper(client: "Client", message: Message) -> Any:
            # Apply the same edit-safe patch as on_command — watchers like
            # pmpermit and antiflood may also try to edit messages they
            # don't own.
            _patch_message_edit(message)
            try:
                return await func(client, message)
            except Exception as exc:
                LOGS.exception("Error in event handler (%s): %s", plugin_name, exc)

        handler = MessageHandler(wrapper, filter_obj)
        from astralbot import clients
        registered = []
        for c in clients or []:
            try:
                c.add_handler(handler, group)
                registered.append((c, handler, group))
            except Exception as exc:
                LOGS.warning("Failed to register event handler: %s", exc)
        _handler_registry.setdefault(plugin_name, []).extend(registered)
        return wrapper

    return decorator


# ---- Hot-unload helpers (called by PluginLoader) ----

def _remove_handlers_for_plugin(plugin_name: str, clients: list) -> None:
    entries = _handler_registry.pop(plugin_name, [])
    for client, handler, group in entries:
        try:
            client.remove_handler(handler, group)
        except Exception:
            pass


def _remove_handlers_for_module(full_module_name: str, clients: list) -> None:
    """Remove handlers for a plugin given its full Python module name."""
    plugin_name = _module_to_plugin.get(full_module_name)
    if plugin_name:
        _remove_handlers_for_plugin(plugin_name, clients)
    else:
        # Best-effort: try the stem
        stem = full_module_name.rsplit(".", 1)[-1]
        if stem.startswith("astralbot_plugin_"):
            stem = stem[len("astralbot_plugin_"):]
        _remove_handlers_for_plugin(stem, clients)

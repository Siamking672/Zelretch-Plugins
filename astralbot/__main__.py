"""
AstralBot entry point.

Run with::

    python -m astralbot

If `.env` doesn't exist (or is missing API_ID / API_HASH), this auto-launches
the setup wizard — a Flask web UI on http://127.0.0.1:8080 that walks the
user through:

  1. Required config (API_ID, API_HASH, optional BOT_TOKEN, etc.)
  2. Userbot session creation (interactive phone → code → 2FA). SKIPPABLE.
  3. Review + Deploy button.

On Deploy, the wizard writes `.env` and starts the bot in a subprocess.

To bypass the wizard check (e.g. for headless deploys where .env is already
populated), pass `--no-wizard`. To force the wizard even when .env exists,
pass `--setup`.

Startup sequence once config is in place:

1. Parse --safe flag (auto-rescue after a crash on previous boot)
2. Load + validate Config (hard-fail on missing required vars)
3. Setup logging (file + console + optional Telegram)
4. Open database (Mongo if DATABASE_URL set, else SQLite)
5. Build Pyrogram clients (primary + optional assistant bot + DB sessions)
6. Bind the global ``Config / client / clients / db / LOGS`` into astralbot.*
7. Pull latest external plugins (updater)
8. Load all plugins (builtins first; skip external in safe mode)
9. Send "started" notice to LOG_CHAT_ID
10. idle() until interrupted

On any uncaught exception during startup, attempt a `--safe` restart.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from astralbot import __version__, _bind_startup_objects
from astralbot.core.config import Config, ConfigError
from astralbot.core.database import open_database
from astralbot.core.client import build_clients, stop_clients
from astralbot.core.loader import PluginLoader
from astralbot.core.logger import setup_logging
from astralbot.core.updater import clone_or_pull_plugin_repo, restart_process


def _is_safe_mode() -> bool:
    return "--safe" in sys.argv


def _wants_setup() -> bool:
    return "--setup" in sys.argv


def _wants_no_wizard() -> bool:
    return "--no-wizard" in sys.argv


def _dotenv_path() -> Path:
    """Where to look for .env.

    Priority:
      1. $DOTENV_PATH env var (set by the wizard when it starts the bot)
      2. /data/.env on HuggingFace Spaces with persistent storage
      3. userdata/.env on HuggingFace Spaces without persistent storage
      4. ./.env locally
    """
    explicit = os.environ.get("DOTENV_PATH")
    if explicit:
        return Path(explicit)
    # Try to import the HF detection helper without failing
    try:
        from astralbot.setup_wizard import get_persistent_env_path
        return get_persistent_env_path()
    except ImportError:
        return Path(".env")


async def main() -> int:
    # 1. Safe mode?
    safe_mode = _is_safe_mode()

    # 2. Config (with graceful error message)
    try:
        config = Config.from_env()
    except ConfigError as exc:
        print(f"[FATAL] Configuration error:\n  {exc}", file=sys.stderr)
        return 1

    # 3. Logging (initial — before Telegram client exists)
    logs = setup_logging(
        log_path=config.data_dir / "astralbot.log",
        log_chat_id=config.log_chat_id,
    )
    logs.info("=" * 60)
    logs.info("AstralBot v%s starting (safe_mode=%s)", __version__, safe_mode)
    logs.info("=" * 60)

    # 4. Build Pyrogram clients FIRST (needed for Telegram channel DB creation)
    try:
        clients = await build_clients(config, db=None)  # type: ignore[arg-type]
    except Exception as exc:
        logs.exception("Client startup failed: %s", exc)
        return 3

    if not clients:
        logs.error(
            "No clients could be started. Check STRING_SESSION / BOT_TOKEN in .env. "
            "Run `python -m astralbot.setup` to reconfigure."
        )
        return 3

    # 5. Auto-create a database channel if DATABASE_URL is not set and we have
    #    a userbot account. This channel will be used as the database backend
    #    (so plugin state survives container restarts on HF Spaces without
    #    persistent storage).
    if config.string_session and not config.database_url and not config.database_chat_id:
        from astralbot.core.client import ensure_database_channel
        await ensure_database_channel(config, clients)

    # 6. Open database — now we have clients available for TelegramChannelDatabase
    try:
        db = await open_database(config, clients=clients)
    except Exception as exc:
        logs.exception("Database open failed: %s", exc)
        await stop_clients(clients)
        return 2

    # 7. Bind globals (so plugins' `from astralbot import ...` works)
    primary = clients[0]
    _bind_startup_objects(config, primary, clients, db, logs)

    # 7.5. Auto-create a log channel if LOG_CHAT_ID is not set.
    # This uses the userbot account to create a private channel, adds the
    # assistant bot as admin, and persists the ID to .env.
    if config.string_session and not config.log_chat_id:
        from astralbot.core.client import ensure_log_channel
        await ensure_log_channel(config, clients)

    # Re-setup logging with the Telegram handler now that we have a client.
    # Uses the async version which verifies LOG_CHAT_ID is reachable before
    # installing the handler — if it's invalid, the handler is skipped with
    # a clear warning instead of silently failing on every subsequent log call.
    from astralbot.core.logger import setup_logging_async
    logs = await setup_logging_async(
        log_path=config.data_dir / "astralbot.log",
        telegram_client=primary,
        log_chat_id=config.log_chat_id,
    )

    # 7. Pull external plugins (skip in safe mode)
    if not safe_mode:
        try:
            await clone_or_pull_plugin_repo(config)
        except Exception as exc:
            logs.warning("External plugin update failed: %s", exc)
    else:
        logs.warning("Safe mode active — external plugins will be skipped.")

    # 8. Load plugins
    loader = PluginLoader(config, clients)
    try:
        loaded = await loader.load_all(safe_mode=safe_mode)
        successful = sum(1 for m in loaded.values() if m.status == "loaded")
        failed = sum(1 for m in loaded.values() if m.status == "failed")
        disabled = sum(1 for m in loaded.values() if m.status == "disabled")
        logs.info(
            "Plugins loaded: %d ok, %d failed, %d disabled", successful, failed, disabled
        )
    except Exception as exc:
        logs.exception("Plugin loader crashed: %s", exc)
        # Continue — builtins might still be loaded

    # 9. Notice to log chat
    if config.log_chat_id:
        try:
            me = await primary.get_me()
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            await primary.send_message(
                config.log_chat_id,
                f"✅ <b>AstralBot v{__version__}</b> started.\n"
                f"Account: @{me.username} (`{me.id}`)\n"
                f"Time: `{now}`\n"
                f"Safe mode: `{safe_mode}`",
            )
        except Exception as exc:
            logs.debug("Failed to send startup notice: %s", exc)

    # 10. Idle
    logs.info("AstralBot is now running. Press Ctrl+C to stop.")
    try:
        await pyrogram_idle()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass

    # Shutdown
    logs.info("Shutting down...")
    await stop_clients(clients)
    await db.close()
    logs.info("Goodbye.")
    return 0


async def pyrogram_idle() -> None:
    """Block until the bot is stopped.

    Pyrogram's built-in ``idle()`` tries to register SIGINT/SIGTERM handlers,
    which fails with ``ValueError: signal only works in main thread of the
    main interpreter`` when the bot is running in a background thread (as it
    does on HuggingFace Spaces, where the main thread runs the Flask wizard).

    We detect whether we're in the main thread:
      - Main thread → use pyrogram.idle() (gets graceful shutdown on Ctrl+C)
      - Background thread → use an asyncio.Event that never fires (the bot
        runs until the process is killed by HF Spaces or the container exits)
    """
    import threading
    if threading.current_thread() is threading.main_thread():
        # Main thread — safe to use pyrogram.idle() with signal handlers
        from pyrogram import idle
        await idle()
    else:
        # Background thread (HF Spaces mode) — signals not allowed.
        # Block forever on an event that never fires. The bot will be killed
        # when the parent process exits (which is what we want on HF Spaces).
        import asyncio
        await asyncio.Event().wait()


def run() -> None:
    """Synchronous entry point used by `python -m astralbot`."""
    # Wizard auto-launch check
    if not _wants_no_wizard() and not _is_safe_mode():
        from astralbot.setup_wizard import should_run_wizard, run_wizard
        env_path = _dotenv_path()
        if _wants_setup() or should_run_wizard(env_path):
            rc = run_wizard(env_path=env_path)
            # After the wizard exits, the bot is already running in a subprocess
            # (started by the wizard). We just exit here.
            sys.exit(rc)

    try:
        rc = asyncio.run(main())
    except KeyboardInterrupt:
        rc = 0
    except Exception as exc:
        traceback.print_exc()
        # Auto-rescue: restart in safe mode unless we're already in safe mode
        if not _is_safe_mode():
            print("\n[FATAL] Startup crashed. Restarting in safe mode...", file=sys.stderr)
            try:
                # Give the user a moment to read the trace
                import time
                time.sleep(3)
                restart_process()
            except Exception:
                pass
        rc = 99
    sys.exit(rc)


if __name__ == "__main__":
    run()

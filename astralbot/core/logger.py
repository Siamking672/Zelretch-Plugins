"""
Logging setup.

Combines best practices from both source projects:
- Rotating file handler (Zelretch style: 5 MB x 10 backups)
- Console handler with colour-free format
- Optional Telegram log channel handler (NEW — neither source had this)
  that forwards WARNING+ to LOG_CHAT_ID for hosted deployments where SSH
  access is unavailable (FoxUserbot had no error reporter at all).

The TelegramLogHandler verifies the chat is reachable before installing
itself — if the user provides an invalid LOG_CHAT_ID (or the bot isn't a
member of that chat), the handler is skipped with a clear warning instead
of silently failing on every log message.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class TelegramLogHandler(logging.Handler):
    """Forward WARNING+ log records to a Telegram chat (async, non-blocking).

    Verifies the chat is reachable on first emit. If the chat is invalid or
    the bot lacks send permission, the handler disables itself to avoid
    spamming silent errors on every subsequent log call.
    """

    # Max consecutive failures before disabling
    MAX_FAILURES = 5

    def __init__(self, client, chat_id: int, level=logging.WARNING):
        super().__init__(level)
        self._client = client
        self._chat_id = chat_id
        self._queue: asyncio.Queue[logging.LogRecord] = asyncio.Queue(maxsize=200)
        self._task: asyncio.Task | None = None
        self._consecutive_failures = 0
        self._disabled = False

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._pump())

    def emit(self, record: logging.LogRecord) -> None:
        if self._disabled:
            return
        try:
            self._queue.put_nowait(record)
        except asyncio.QueueFull:
            # Drop oldest to make room — never block logging
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(record)
            except Exception:
                pass

    async def _pump(self) -> None:
        while True:
            record = await self._queue.get()
            if self._disabled:
                continue
            try:
                text = self.format(record)
                if len(text) > 3900:
                    text = text[:3900] + "\n... (truncated)"
                await self._client.send_message(self._chat_id, f"```\n{text}\n```")
                # Reset failure counter on success
                self._consecutive_failures = 0
            except Exception as exc:
                self._consecutive_failures += 1
                # If we've failed too many times, disable the handler
                if self._consecutive_failures >= self.MAX_FAILURES:
                    self._disabled = True
                    # Log to stderr once so the user knows why logs stopped
                    try:
                        print(
                            f"[astralbot.logger] TelegramLogHandler disabled after "
                            f"{self._consecutive_failures} consecutive failures. "
                            f"Last error: {exc}. LOG_CHAT_ID={self._chat_id}",
                            file=sys.stderr,
                        )
                    except Exception:
                        pass
                # Never let a logging failure crash the bot
                continue


async def _verify_log_chat(client, chat_id: int) -> bool:
    """Probe whether the bot can send messages to the given chat.

    Returns True if the chat is reachable, False otherwise. We do this by
    attempting to fetch the chat (cheap, doesn't send a message).
    """
    try:
        await client.get_chat(chat_id)
        return True
    except Exception:
        return False


def setup_logging(log_path: Path | str = "astralbot.log", telegram_client=None, log_chat_id: int | None = None) -> logging.Logger:
    """Configure root logger with file + console, and optional Telegram sink.

    Synchronous version — installs the TelegramLogHandler without verifying
    the chat (verification requires async). Use ``setup_logging_async`` if
    you have a running event loop and want the verification step.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    # Wipe any pre-existing handlers (prevents duplicate output across reloads)
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(logging.INFO)

    file_h = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_h.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(file_h)

    console_h = logging.StreamHandler(sys.stdout)
    console_h.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console_h)

    # Suppress noisy third-party loggers
    for noisy in ("pyrogram", "kurigram", "urllib3", "asyncio", "motor"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    if telegram_client is not None and log_chat_id:
        tg_h = TelegramLogHandler(telegram_client, log_chat_id, level=logging.WARNING)
        tg_h.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        tg_h.start()
        root.addHandler(tg_h)

    logs = logging.getLogger("astralbot")
    logs.info("Logging initialised → file=%s, telegram=%s", log_path, bool(log_chat_id))
    return logs


async def setup_logging_async(log_path: Path | str = "astralbot.log", telegram_client=None, log_chat_id: int | None = None) -> logging.Logger:
    """Async version of setup_logging that verifies LOG_CHAT_ID is reachable.

    If the chat is invalid or the bot lacks permission, the Telegram handler
    is skipped with a clear warning — instead of silently failing on every
    subsequent log call.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(logging.INFO)

    file_h = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_h.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(file_h)

    console_h = logging.StreamHandler(sys.stdout)
    console_h.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console_h)

    for noisy in ("pyrogram", "kurigram", "urllib3", "asyncio", "motor"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logs = logging.getLogger("astralbot")

    telegram_ok = False
    if telegram_client is not None and log_chat_id:
        # Verify the chat is reachable before installing the handler
        telegram_ok = await _verify_log_chat(telegram_client, log_chat_id)
        if telegram_ok:
            tg_h = TelegramLogHandler(telegram_client, log_chat_id, level=logging.WARNING)
            tg_h.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            tg_h.start()
            root.addHandler(tg_h)
        else:
            logs.warning(
                "LOG_CHAT_ID=%s is unreachable (bot not a member, or invalid ID). "
                "Telegram log forwarding disabled. To fix: create a Telegram channel/group, "
                "add the bot as admin, then set LOG_CHAT_ID to that chat's ID.",
                log_chat_id,
            )

    logs.info("Logging initialised → file=%s, telegram=%s", log_path, telegram_ok)
    return logs

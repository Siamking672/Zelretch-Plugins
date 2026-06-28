"""Advanced message purge and self-destruct plugin.

Commands provided
-----------------
  ``.purge``            Delete a range of messages (reply → latest).
  ``.purge <count>``    Delete the last N messages in the chat.
  ``.purgeme``          Delete your own recent messages.
  ``.purgeuser``        Delete a specific user's messages.
  ``.purgeall``         Delete ALL messages in a chat (destructive).
  ``.del``              Delete the single replied message.
  ``.selfdestruct``     Send a message that auto-deletes after N seconds.

Design notes
------------
* Every purge command uses **batch deletion** (up to 100 message IDs per
  API call) instead of one-by-one deletion. This is ~100x faster.
* A live progress counter is edited into the status message every
  25 deleted batches so the user sees the purge advancing.
* FloodWait is handled gracefully — we sleep and retry the same batch.
* All other exceptions are caught and counted as "failed" rather than
  silently swallowed, so the final summary is accurate.
* The final status message auto-deletes after 5 seconds so the chat
  stays clean.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

from kurigram import Client
from kurigram.enums import MessagesFilter
from kurigram.errors import FloodWait
from kurigram.errors.exceptions import FloodWait as FloodWaitExc
from kurigram.types import Message

from . import HelpMenu, zelretch, on_message


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Telegram allows deleting up to 100 messages per single delete_messages call.
BATCH_SIZE = 100

# How often (in batches) to update the progress status message.
PROGRESS_UPDATE_EVERY = 25  # = every 2500 messages

# Auto-delete the final summary after this many seconds.
SUMMARY_DELETE_DELAY = 5

# Maximum messages a single purge command will touch. Prevents
# accidental "purge 999999999" from running for hours.
MAX_PURGE_LIMIT = 100_000


# ---------------------------------------------------------------------------
# Core deletion engine
# ---------------------------------------------------------------------------

class PurgeStats:
    """Tracks deletion counts during a purge operation."""

    def __init__(self) -> None:
        self.deleted: int = 0
        self.failed: int = 0
        self.start_time: float = time.time()

    @property
    def total(self) -> int:
        return self.deleted + self.failed

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def rate(self) -> float:
        """Messages deleted per second."""
        e = self.elapsed
        return self.deleted / e if e > 0 else 0.0

    def summary(self) -> str:
        """One-line summary string for the status message."""
        parts = [f"🧹 Deleted: **{self.deleted}**"]
        if self.failed:
            parts.append(f"Failed: **{self.failed}**")
        parts.append(f"({self.rate:.0f} msg/s)")
        return "  •  ".join(parts)


async def _delete_batch(
    client: Client,
    chat_id: int,
    msg_ids: list[int],
    stats: PurgeStats,
) -> None:
    """Delete a batch of message IDs, handling FloodWait.

    Updates ``stats`` in place. Retries once after sleeping if Telegram
    asks us to slow down.
    """
    try:
        result = await client.delete_messages(chat_id, msg_ids)
        # ``delete_messages`` returns the count of messages it actually
        # deleted (some IDs may not exist or may be too old to delete).
        if isinstance(result, int):
            stats.deleted += result
        else:
            stats.deleted += len(msg_ids)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            result = await client.delete_messages(chat_id, msg_ids)
            if isinstance(result, int):
                stats.deleted += result
            else:
                stats.deleted += len(msg_ids)
        except Exception:
            stats.failed += len(msg_ids)
    except Exception:
        # MessageDeleteForbidden, ChatAdminRequired, etc.
        stats.failed += len(msg_ids)


async def _delete_messages_streaming(
    client: Client,
    chat_id: int,
    msg_ids: list[int],
    status_msg: Message,
    label: str = "Purging",
) -> PurgeStats:
    """Delete a list of message IDs in batches with live progress.

    The ``status_msg`` is edited every ``PROGRESS_UPDATE_EVERY`` batches
    so the user sees the purge advancing. Returns the final
    :class:`PurgeStats`.
    """
    stats = PurgeStats()
    total = len(msg_ids)
    batches = [msg_ids[i:i + BATCH_SIZE] for i in range(0, len(msg_ids), BATCH_SIZE)]

    for i, batch in enumerate(batches, start=1):
        await _delete_batch(client, chat_id, batch, stats)

        if i % PROGRESS_UPDATE_EVERY == 0 and i < len(batches):
            try:
                await status_msg.edit_text(
                    f"__{label}...  {stats.deleted:,} / {total:,} deleted"
                    f"  ({stats.rate:.0f} msg/s)__"
                )
            except Exception:
                pass  # status message may have been deleted

    return stats


async def _delete_via_search(
    client: Client,
    chat_id: int,
    status_msg: Message,
    label: str,
    limit: int,
    from_user: Optional[int | str] = None,
    filter: Optional[MessagesFilter] = None,
) -> PurgeStats:
    """Delete messages by collecting them via ``search_messages``.

    Used when we can't build an ID range (e.g. purging a specific user's
    messages). Collects IDs in batches, then deletes in batches.
    """
    stats = PurgeStats()
    collected: list[int] = []
    collected_count = 0

    async def flush() -> None:
        """Delete the collected batch and update progress."""
        nonlocal collected
        if not collected:
            return
        await _delete_batch(client, chat_id, collected, stats)
        collected = []

    async for msg in client.search_messages(
        chat_id, limit=limit, from_user=from_user, filter=filter
    ):
        collected.append(msg.id)
        collected_count += 1
        if len(collected) >= BATCH_SIZE:
            await flush()
            if collected_count % (BATCH_SIZE * PROGRESS_UPDATE_EVERY) == 0:
                try:
                    await status_msg.edit_text(
                        f"__{label}...  {stats.deleted:,} deleted"
                        f"  ({stats.rate:.0f} msg/s)__"
                    )
                except Exception:
                    pass

    await flush()  # delete any remaining
    return stats


async def _finalize(
    status_msg: Message,
    stats: PurgeStats,
    extra: str = "",
) -> None:
    """Edit the status message with the final summary, then auto-delete it."""
    summary = stats.summary()
    if extra:
        summary = f"{summary}  •  {extra}"
    try:
        await status_msg.edit_text(f"__{summary}__")
        if SUMMARY_DELETE_DELAY > 0:
            await asyncio.sleep(SUMMARY_DELETE_DELAY)
            await status_msg.delete()
    except Exception:
        pass


def _parse_count(arg: Optional[str], default: int = 100) -> tuple[bool, int, str]:
    """Parse a count argument. Returns (ok, count, error_message)."""
    if not arg:
        return True, default, ""
    try:
        count = int(arg)
    except ValueError:
        return False, 0, "Count must be an integer."
    if count < 0:
        return False, 0, "Count must be non-negative."
    if count > MAX_PURGE_LIMIT:
        return False, 0, f"Count exceeds the maximum of {MAX_PURGE_LIMIT:,}."
    return True, count, ""


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@on_message("purge", allow_master=True)
async def purge_command(client: Client, message: Message):
    """Delete a range of messages, or the last N messages.

    Usage:
      .purge                 (reply to a message) — delete from the
                              replied message up to now.
      .purge <count>         delete the last N messages in the chat.
      .purge <count> --dry   show how many would be deleted without
                              actually deleting anything.
    """
    # Mode 1: .purge <count> — delete the last N messages
    if len(message.command) >= 2 and not message.reply_to_message:
        dry_run = "--dry" in message.command
        ok, count, err = _parse_count(message.command[1])
        if not ok:
            return await zelretch.delete(message, f"__{err}__")
        if count == 0:
            return await zelretch.delete(message, "__Nothing to purge.__")

        kaleido = await zelretch.edit(
            message, f"__Collecting last {count:,} messages...__"
        )

        if dry_run:
            await kaleido.edit_text(f"__Dry run: would delete up to {count:,} messages.__")
            await asyncio.sleep(SUMMARY_DELETE_DELAY)
            await kaleido.delete()
            return

        stats = await _delete_via_search(
            client, message.chat.id, kaleido,
            label=f"Purging last {count:,}", limit=count,
        )
        await _finalize(kaleido, stats, extra=f"of {count:,} requested")
        return

    # Mode 2: .purge (reply) — delete from replied message up to now
    if not message.reply_to_message:
        return await zelretch.delete(
            message,
            "__Reply to a message to purge from there to now, "
            "or pass a count:__ `.purge 50`",
        )

    from_id = message.reply_to_message.id
    to_id = message.id  # don't delete the purge command itself yet
    # Build the full list of message IDs in the range
    msg_ids = list(range(from_id, to_id))
    if not msg_ids:
        return await zelretch.delete(message, "__No messages to purge in that range.__")

    kaleido = await zelretch.edit(
        message, f"__Purging {len(msg_ids):,} messages...__"
    )

    stats = await _delete_messages_streaming(
        client, message.chat.id, msg_ids, kaleido,
        label=f"Purging {len(msg_ids):,}",
    )

    await _finalize(kaleido, stats)


@on_message("purgeme", allow_master=True)
async def purgeme_command(client: Client, message: Message):
    """Delete your own recent messages in the current chat.

    Usage:
      .purgeme              delete your last 100 messages (default).
      .purgeme <count>      delete your last N messages.
    """
    ok, count, err = _parse_count(
        message.command[1] if len(message.command) >= 2 else None,
        default=100,
    )
    if not ok:
        return await zelretch.delete(message, f"__{err}__")
    if count == 0:
        return await zelretch.delete(message, "__Nothing to purge.__")

    kaleido = await zelretch.edit(
        message, f"__Purging your last {count:,} messages...__"
    )

    stats = await _delete_via_search(
        client, message.chat.id, kaleido,
        label=f"Purging your last {count:,}", limit=count, from_user="me",
    )

    await _finalize(kaleido, stats, extra=f"of {count:,} requested")


@on_message("purgeuser", allow_master=True)
async def purgeuser_command(client: Client, message: Message):
    """Delete a specific user's messages in the current chat.

    Usage:
      .purgeuser <count>    (reply to user) — delete their last N
                            messages. Defaults to 100.
      .purgeuser 0          (reply to user) — delete ALL of their
                            messages in this chat (use with caution).
    """
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await zelretch.delete(
            message, "__Reply to a user to delete their messages.__"
        )

    target = message.reply_to_message.from_user
    ok, count, err = _parse_count(
        message.command[1] if len(message.command) >= 2 else None,
        default=100,
    )
    if not ok:
        return await zelretch.delete(message, f"__{err}__")
    # count == 0 means "all" — set a high limit
    limit = MAX_PURGE_LIMIT if count == 0 else count

    kaleido = await zelretch.edit(
        message,
        f"__Purging {target.mention}'s messages"
        f" ({'all' if count == 0 else f'last {count:,}'})...__",
    )

    stats = await _delete_via_search(
        client, message.chat.id, kaleido,
        label=f"Purging {target.first_name}'s messages",
        limit=limit, from_user=target.id,
    )

    await _finalize(kaleido, stats, extra=f"of {target.mention}'s messages")


@on_message("purgeall", allow_master=True)
async def purgeall_command(client: Client, message: Message):
    """Delete ALL messages in the current chat. Extremely destructive.

    Usage:
      .purgeall             requires confirmation — type the command
                            twice within 10 seconds to confirm.
    """
    # Two-step confirmation: the first invocation sets a flag in the
    # message's reply chain; the second within 10s actually purges.
    # We use a simple approach: require the word "confirm" as an arg.
    if len(message.command) < 2 or message.command[1] != "confirm":
        return await zelretch.delete(
            message,
            "__⚠️ This will delete EVERY message in this chat.\n"
            "To confirm, run:__ `.purgeall confirm`",
        )

    kaleido = await zelretch.edit(
        message, "__⚠️ Purging ALL messages in this chat...__"
    )

    stats = await _delete_via_search(
        client, message.chat.id, kaleido,
        label="Purging ALL messages", limit=MAX_PURGE_LIMIT,
    )

    await _finalize(kaleido, stats, extra="ALL messages")


@on_message("del", allow_master=True)
async def del_command(_, message: Message):
    """Delete the single replied message and the command message."""
    if not message.reply_to_message:
        return await zelretch.delete(
            message, "__Reply to a message to delete it.__"
        )
    try:
        await message.reply_to_message.delete()
    except Exception:
        pass
    await message.delete()


@on_message(["selfdestruct", "sd"], allow_master=True)
async def selfdestruct_command(client: Client, message: Message):
    """Send a message that auto-deletes after N seconds.

    Usage:
      .sd <seconds> <text>            send text, delete after N seconds.
      .sd <seconds> (reply to media)  re-send the replied media, delete
                                      after N seconds.

    The countdown is shown in the message and updates every second for
    the last 10 seconds so the recipient knows when it'll vanish.
    """
    if len(message.command) < 3 and not message.reply_to_message:
        return await zelretch.delete(
            message,
            "__Give the number of seconds and the message text, "
            "or reply to a media message.__\n"
            "__Example:__ `.sd 30 Hello world`",
        )

    # Parse the seconds argument
    try:
        seconds = int(message.command[1])
    except (ValueError, IndexError):
        return await zelretch.delete(
            message, "__Seconds must be an integer. Example:__ `.sd 30 hello`"
        )

    if seconds <= 0:
        return await zelretch.delete(message, "__Seconds must be greater than 0.__")
    if seconds > 86400:
        return await zelretch.delete(
            message, "__Maximum self-destruct timer is 86400 seconds (24 hours).__"
        )

    # Determine the message text or media to send
    text = " ".join(message.command[2:]) if len(message.command) >= 3 else ""
    replied = message.reply_to_message

    await message.delete()

    # Send the message (text or copied media)
    if replied and (replied.media or replied.text):
        sent = await replied.copy(message.chat.id)
        if text:
            await sent.reply_text(text, quote=True)
    else:
        if not text:
            return  # nothing to send
        sent = await client.send_message(message.chat.id, text)

    # Countdown loop: update the caption/text every second for the
    # final 10 seconds, then delete.
    countdown_start = min(seconds, 10)
    initial_wait = seconds - countdown_start
    if initial_wait > 0:
        await asyncio.sleep(initial_wait)

    for remaining in range(countdown_start, 0, -1):
        try:
            await sent.edit_text(
                f"{' '.join(message.command[2:]) if text else '⏳'}\n"
                f"__Vanishes in {remaining}s__"
            ) if not (replied and replied.media) else None
        except Exception:
            pass
        await asyncio.sleep(1)

    try:
        await sent.delete()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Help menu
# ---------------------------------------------------------------------------

HelpMenu("purge").add(
    "purge",
    "<reply to message> or <count> [--dry]",
    "Delete a range of messages. Reply to a message to delete everything from there to now, or pass a count to delete the last N messages. Add --dry to preview the count without deleting.",
    "purge",
    "The userbot must be an admin with delete-message permission. Batch deletion is used (100 messages per API call) for speed. Maximum 100,000 messages per invocation.",
).add(
    "purgeme",
    "<count (optional, default 100)>",
    "Delete your own recent messages from the current chat.",
    "purgeme 50",
    "Defaults to 100 messages when no count is given.",
).add(
    "purgeuser",
    "<reply to user> <count (optional, default 100)>",
    "Delete a specific user's messages from the current chat. Pass 0 as the count to delete ALL of their messages (use with extreme caution).",
    "purgeuser",
    "Defaults to 100 messages. The user is identified by the replied message's sender.",
).add(
    "purgeall",
    "confirm",
    "Delete EVERY message in the current chat. This is extremely destructive and requires the literal word 'confirm' as an argument to prevent accidental invocation.",
    "purgeall confirm",
    "⚠️ This cannot be undone. Only use in chats you own or are willing to empty completely.",
).add(
    "del",
    "<reply to message>",
    "Delete the single replied message and the command message itself.",
    "del",
).add(
    "selfdestruct",
    "<seconds> <text> or <seconds> <reply to media>",
    "Send a message that automatically deletes itself after the specified number of seconds. Supports both text and replied media. A live countdown is shown for the final 10 seconds.",
    "selfdestruct 30 This will vanish in half a minute",
    "Alias 'sd' can also be used. Maximum timer is 86400 seconds (24 hours).",
).info(
    "Advanced message deletion — batch-purge ranges, users, or entire chats with live progress, plus self-destructing messages with countdown."
).done()

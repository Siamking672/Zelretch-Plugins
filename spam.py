# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}spam <count> <text>`
    Repeat text N times as separate messages (max 20).

• `{i}spamstick <count>`
    Send the replied sticker N times (max 20).

• `{i}dspam <delay> <count> <text>`
    Delayed spam with a delay between messages.
"""

from __future__ import annotations

import asyncio

from plugins import eod, eor, zelretch_bot, zelretch_cmd


@zelretch_cmd(pattern=r"spam\s+(\d+)\s+(.+)$", owner_only=True)
async def spam(event):
    n = int(event.matches[0].group(1))
    text = event.matches[0].group(2)
    if n > 20:
        return await eod(event, "Maximum spam count is 20.", time=5)
    if zelretch_bot is None:
        return
    for _ in range(n):
        try:
            await event.reply(text)
        except Exception:
            break


@zelretch_cmd(pattern=r"spamstick\s+(\d+)$", owner_only=True)
async def spamstick(event):
    n = int(event.matches[0].group(1))
    if n > 20:
        return await eod(event, "Maximum spam count is 20.", time=5)
    if not event.reply_to_message or not event.reply_to_message.sticker:
        return await eod(event, "Reply to a sticker first.", time=5)
    sticker = event.reply_to_message.sticker.file_id
    if zelretch_bot is None:
        return
    for _ in range(n):
        try:
            await zelretch_bot.send_sticker(event.chat.id, sticker)
        except Exception:
            break


@zelretch_cmd(pattern=r"dspam\s+(\d+)\s+(\d+)\s+(.+)$", owner_only=True)
async def dspam(event):
    delay = int(event.matches[0].group(1))
    n = int(event.matches[0].group(2))
    text = event.matches[0].group(3)
    if n > 20:
        return await eod(event, "Maximum spam count is 20.", time=5)
    for _ in range(n):
        try:
            await event.reply(text)
            await asyncio.sleep(delay)
        except Exception:
            break

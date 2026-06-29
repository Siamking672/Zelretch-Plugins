# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}stickerspam <count>`
    Spam the replied sticker N times (max 30).
"""

from __future__ import annotations

from plugins import eod, zelretch_bot, zelretch_cmd


@zelretch_cmd(pattern=r"stickerspam\s+(\d+)$", owner_only=True)
async def stickerspam(event):
    n = int(event.matches[0].group(1))
    if n > 30:
        return await eod(event, "Max 30 stickers per spam.", time=5)
    if not event.reply_to_message or not event.reply_to_message.sticker:
        return await eod(event, "Reply to a sticker.", time=5)
    if zelretch_bot is None:
        return
    sid = event.reply_to_message.sticker.file_id
    for _ in range(n):
        try:
            await zelretch_bot.send_sticker(event.chat.id, sid)
        except Exception:
            break

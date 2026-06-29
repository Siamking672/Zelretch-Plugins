# Zelretch Addons — Spam tool
# Ported from UltroidAddons/spam.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}spam <count> <message>`
    Send a message N times (owner only). Use responsibly.

• `{i}dspam <delay> <count> <message>`
    Delayed spam — N times with M seconds between.
"""

import asyncio

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"spam (\d+) (.+)", owner_only=True)
async def spam(client, message):
    try:
        count = int(message.matches[0].group(1))
        text = message.matches[0].group(2)
    except (AttributeError, IndexError, ValueError):
        return await eor(message, "`Usage: .spam <count> <message>`")
    if count > 100:
        return await eor(message, "`Max 100 messages per spam.`")
    for _ in range(count):
        try:
            await client.send_message(message.chat.id, text)
        except Exception:
            break
    await message.delete()


@zelretch_cmd(pattern=r"dspam (\d+) (\d+) (.+)", owner_only=True)
async def dspam(client, message):
    try:
        delay = float(message.matches[0].group(1))
        count = int(message.matches[0].group(2))
        text = message.matches[0].group(3)
    except (AttributeError, IndexError, ValueError):
        return await eor(message, "`Usage: .dspam <delay> <count> <message>`")
    if count > 100:
        return await eor(message, "`Max 100 messages per spam.`")
    for _ in range(count):
        try:
            await client.send_message(message.chat.id, text)
        except Exception:
            break
        await asyncio.sleep(delay)
    await message.delete()

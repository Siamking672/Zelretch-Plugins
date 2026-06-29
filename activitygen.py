# Zelretch Addons — Activity generator
# Ported from UltroidAddons/activitygen.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}activity <count>`
    Send N "typing…" indicators (no actual message) — useful for testing.
"""

import asyncio

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor

try:
    from kurigram.enums import ChatAction
    CHAT_ACTION_AVAILABLE = True
except ImportError:  # pragma: no cover
    CHAT_ACTION_AVAILABLE = False


@zelretch_cmd(pattern=r"activity (\d+)", owner_only=True)
async def activity(client, message):
    if not CHAT_ACTION_AVAILABLE:
        return await eor(message, "`kurigram ChatAction not available.`")
    n = int(message.matches[0].group(1))
    if n > 50:
        return await eor(message, "`Max 50.`")
    await message.delete()
    for _ in range(n):
        try:
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        except Exception:
            break
        await asyncio.sleep(2)

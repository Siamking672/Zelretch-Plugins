# Zelretch Addons — Hack text animation
# Ported from UltroidAddons/hack.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}hack`
    Play a fake "hacking" animation. (Just for fun.)
"""

import asyncio
import random

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor

STEPS = [
    "Initializing hack framework…",
    "Connecting to Telegram servers…",
    "Bypassing 2FA…",
    "Decrypting session strings…",
    "Dumping message history…",
    "Hiding traces…",
    "Hack complete. Root access obtained. (just kidding 🤡)",
]


@zelretch_cmd(pattern="hack$")
async def hack(client, message):
    msg = await message.reply_text(STEPS[0])
    for step in STEPS[1:]:
        await asyncio.sleep(1.0 + random.random() * 0.8)
        try:
            await msg.edit_text(step)
        except Exception:
            pass

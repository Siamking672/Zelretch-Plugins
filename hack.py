# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}hack`
    Fake "hacking" animation, just for fun.
"""

from __future__ import annotations

import asyncio

from plugins import eor, zelretch_cmd

_STEPS = [
    "Initializing exploit framework...",
    "Bypassing firewall [██████████] 100%",
    "Injecting payload...",
    "Decrypting Telegram session...",
    "Covering tracks...",
    "Done. Access granted. (just kidding 😜)",
]


@zelretch_cmd(pattern="hack$")
async def hack(event):
    msg = await event.reply(_STEPS[0])
    for s in _STEPS[1:]:
        await asyncio.sleep(1.0)
        try:
            await msg.edit(s)
        except Exception:
            pass

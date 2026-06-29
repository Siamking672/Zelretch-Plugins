# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}random`
    Generate a random number between 1 and 100.

• `{i}random <max>`
    Generate a random number between 1 and <max>.

• `{i}random <min> <max>`
    Generate a random number between <min> and <max>.

• `{i}coinflip`
    Flip a coin.
"""

from __future__ import annotations

import random

from plugins import eor, zelretch_cmd


@zelretch_cmd(pattern=r"random(?:\s+(\d+))?(?:\s+(\d+))?$")
async def random_cmd(event):
    g = event.matches[0]
    a, b = g.group(1), g.group(2)
    if a and b:
        n = random.randint(int(a), int(b))
    elif a:
        n = random.randint(1, int(a))
    else:
        n = random.randint(1, 100)
    await eor(event, f"🎲 Random: `{n}`")


@zelretch_cmd(pattern="coinflip$")
async def coinflip(event):
    side = random.choice(["Heads", "Tails"])
    await eor(event, f"🪙 {side}!")

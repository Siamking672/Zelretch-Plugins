# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}activitygen`
    Generate a random "last seen" activity for the bot account.
"""

from __future__ import annotations

import random

from plugins import eor, zelretch_cmd

_ACTIVITIES = [
    "Playing .help",
    "Listening to .ping",
    "Watching the chat",
    "Streaming Zelretch v1.0.0",
    "Competing in userbot wars",
    "Editing messages at the speed of light",
]


@zelretch_cmd(pattern="activitygen$")
async def activitygen(event):
    await eor(event, f"🎮 Suggested activity: `{random.choice(_ACTIVITIES)}`")

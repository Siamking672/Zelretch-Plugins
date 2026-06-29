# Zelretch Addons — Truth or Dare
# Ported from UltroidAddons/truthdare.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}truth`
    Get a random truth question.

• `{i}dare`
    Get a random dare.
"""

import random

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor

TRUTHS = [
    "What's the most embarrassing thing you've done in public?",
    "What's a secret you've never told anyone?",
    "What's the biggest lie you've ever told?",
    "Who do you have a crush on right now?",
    "What's the weirdest dream you've ever had?",
    "What's your biggest fear?",
    "Have you ever pretended to be sick to avoid someone?",
    "What's the most childish thing you still do?",
]

DARES = [
    "Speak in an accent for the next 5 minutes.",
    "Send your last selfie to the chat.",
    "Compliment the person above you for 30 seconds straight.",
    "Do 10 pushups and send proof.",
    "Sing the chorus of your favorite song out loud.",
    "Text 'I love you' to the last person you messaged.",
    "Don't speak for the next 3 rounds.",
    "Do your best dance move and send a video.",
]


@zelretch_cmd(pattern="truth$")
async def truth(client, message):
    await eor(message, f"🤔 **Truth:**\n\n{random.choice(TRUTHS)}")


@zelretch_cmd(pattern="dare$")
async def dare(client, message):
    await eor(message, f"😈 **Dare:**\n\n{random.choice(DARES)}")

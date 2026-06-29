# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}truth`
    Random truth question.

• `{i}dare`
    Random dare.
"""

from __future__ import annotations

import random

from plugins import eor, zelretch_cmd

_TRUTHS = [
    "What is your biggest fear?",
    "What's the most embarrassing thing you've ever done?",
    "Who is your secret crush?",
    "What's the biggest lie you've ever told?",
    "What's the worst gift you've ever received?",
    "Have you ever cheated on a test?",
    "What's your most annoying habit?",
    "What's the weirdest dream you've had?",
]

_DARES = [
    "Sing the chorus of your favorite song.",
    "Talk in a funny voice for the next 5 minutes.",
    "Send a sticker of the last emoji you used.",
    "Tell a joke right now.",
    "Compliment the person above you.",
    "Do 10 jumping jacks.",
    "Send your last photo.",
    "Speak only in questions for the next 5 turns.",
]


@zelretch_cmd(pattern="truth$")
async def truth(event):
    await eor(event, f"🧐 Truth: {random.choice(_TRUTHS)}")


@zelretch_cmd(pattern="dare$")
async def dare(event):
    await eor(event, f"😈 Dare: {random.choice(_DARES)}")

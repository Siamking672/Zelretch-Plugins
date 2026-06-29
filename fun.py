# Zelretch Addons — Fun commands
# Ported from UltroidAddons/fun.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}slap <reply>`
    Slap the replied user with a random item.

• `{i}hug <reply>`
    Hug the replied user.

• `{i}8ball <question>`
    Ask the magic 8-ball.
"""

import random

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor
from zelretch.utils.helpers import inline_mention

SLAP_ITEMS = [
    "a wet noodle", "a Windows ME CD", "a trout", "a rubber chicken",
    "a slice of cold pizza", "an inflamed torque wrench", "a CRT monitor",
    "a stack of overdue homework", "the entire Ultroid codebase",
]

HUGS = [
    "gives {target} a big warm hug 🤗",
    "wraps {target} in a friendly embrace 🤗",
    "sends virtual hugs to {target} 🤗",
]

BALL_RESPONSES = [
    "It is certain.", "Without a doubt.", "Yes — definitely.",
    "You may rely on it.", "Most likely.", "Outlook good.",
    "Yes.", "Signs point to yes.", "Reply hazy, try again.",
    "Ask again later.", "Cannot predict now.", "Don't count on it.",
    "My reply is no.", "Outlook not so good.", "Very doubtful.",
]


@zelretch_cmd(pattern=r"slap( (.*)|$)")
async def slap(client, message):
    reply = message.reply_to_message
    target = reply.from_user if reply and reply.from_user else None
    if target is None:
        return await eor(message, "Reply to someone to slap them.")
    mention = inline_mention(target)
    sender = inline_mention(message.from_user) if message.from_user else "Zelretch"
    item = random.choice(SLAP_ITEMS)
    await eor(message, f"{sender} slaps {mention} with {item}! 👋")


@zelretch_cmd(pattern=r"hug( (.*)|$)")
async def hug(client, message):
    reply = message.reply_to_message
    target = reply.from_user if reply and reply.from_user else None
    if target is None:
        return await eor(message, "Reply to someone to hug them.")
    mention = inline_mention(target)
    action = random.choice(HUGS).format(target=mention)
    await eor(message, f"🤗 {action}")


@zelretch_cmd(pattern=r"8ball ?(.*)")
async def eight_ball(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Ask the magic 8-ball a question.`")
    await eor(message, f"🎱 **Magic 8-Ball says:**\n\n_{random.choice(BALL_RESPONSES)}_")

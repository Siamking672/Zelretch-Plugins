# Zelretch Addons — Wikipedia random facts / quotes
# Ported from UltroidAddons/random.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}quote`
    Get a random inspirational quote.

• `{i}fact`
    Get a random fun fact.

• `{i}joke`
    Get a random programming joke.
"""

import requests

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="quote$")
async def quote(client, message):
    try:
        resp = requests.get("https://api.quotable.io/random", timeout=10)
        data = resp.json()
        await eor(message, f"**{data['content']}**\n\n— _{data['author']}_")
    except Exception as err:
        await eor(message, f"`{err}`")


@zelretch_cmd(pattern="fact$")
async def fact(client, message):
    try:
        resp = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random", timeout=10)
        data = resp.json()
        await eor(message, f"🧠 **Did you know?**\n\n{data['text']}")
    except Exception as err:
        await eor(message, f"`{err}`")


@zelretch_cmd(pattern="joke$")
async def joke(client, message):
    try:
        resp = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=10)
        data = resp.json()
        await eor(message, f"**{data['setup']}**\n\n_{data['punchline']}_")
    except Exception as err:
        await eor(message, f"`{err}`")

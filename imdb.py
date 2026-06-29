# Zelretch Addons — IMDB plugin
# Ported from UltroidAddons/imdb.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}imdb <movie>`
    Search IMDB for movie details (uses inline bot).
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"imdb ?(.*)")
async def imdb(client, message):
    match = message.text.split(maxsplit=1)
    if len(match) < 2 or not match[1].strip():
        return await eor(message, "`Provide a movie name.`")
    movie = match[1].strip()
    msg = await message.reply_text("`Searching IMDB…`")
    try:
        results = await client.inline_query("imdbot", movie)
        if results:
            await results[0].click(message.chat.id)
            await msg.delete()
        else:
            await msg.edit_text("`No results found.`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

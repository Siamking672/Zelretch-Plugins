# Zelretch Addons — Wikipedia plugin
# Ported from UltroidAddons/wikipedia.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}wiki <query>`
    Search Wikipedia from Telegram.
"""

import wikipedia

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"wiki ?(.*)")
async def wiki(client, message):
    query = message.text.split(maxsplit=1)
    if len(query) < 2 or not query[1].strip():
        return await eor(message, "`Give some text to search on Wikipedia.`")
    search = query[1].strip()
    msg = await message.reply_text(f"`Searching {search} on Wikipedia…`")
    try:
        summary = wikipedia.summary(search, sentences=4)
        text = f"**Search Query:** `{search}`\n\n**Result:** {summary}"
        await msg.edit_text(text)
    except wikipedia.exceptions.DisambiguationError as err:
        await msg.edit_text(f"**Disambiguation** — did you mean:\n`{', '.join(err.options[:5])}`")
    except wikipedia.exceptions.PageError:
        await msg.edit_text("`No Wikipedia page matched your query.`")
    except Exception as err:
        await msg.edit_text(f"**ERROR:** `{err}`")

# Zelretch Addons — Howto (how-to do things)
# Ported from UltroidAddons/howto.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}howto <query>`
    Get a quick how-to summary (Wikipedia-style).
"""

import wikipedia

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"howto ?(.*)")
async def howto(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give a query.`")
    query = parts[1].strip()
    msg = await message.reply_text(f"`Looking up how to {query}…`")
    try:
        summary = wikipedia.summary(f"how to {query}", sentences=3, auto_suggest=False)
        await msg.edit_text(f"**How to {query}:**\n\n{summary}")
    except wikipedia.exceptions.DisambiguationError as err:
        await msg.edit_text(f"Be more specific. Did you mean:\n`{', '.join(err.options[:5])}`")
    except wikipedia.exceptions.PageError:
        await msg.edit_text("`No results found.`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

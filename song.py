# Zelretch Addons — Lyrics
# Ported from UltroidAddons/song.py (lyrics command)
# Copyright (C) 2020-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}lyrics <song>`
    Get song lyrics.
"""

import random

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"lyrics ?(.*)")
async def lyrics(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "Give a query to search.")
    query = parts[1].strip()
    msg = await message.reply_text("`Getting lyrics…`")
    try:
        from lyrics_extractor import SongLyrics
        # Use public demo credentials — recommend users replace with their own.
        geni_api_key = random.choice([
            "AIzaSyAyDBsY3WRtB5YPC6aB_w8JAy6ZdXNc6FU",
            "AIzaSyBF0zxLlYlPMp9xwMQqVKCQRq8DgdrLXsg",
            "AIzaSyDdOKnwnPwVIQ_lbH5sYE4FoXjAKIQV0DQ",
        ])
        extractor = SongLyrics(geni_api_key, "15b9fb6193efd5d90")
        result = await _safe_extract(extractor, query)
        if not result or not result.get("lyrics"):
            return await msg.edit_text("`No results found.`")
        text = result["lyrics"]
        if len(text) > 3500:
            text = text[:3500] + "…"
        await msg.edit_text(f"**{result.get('title', query)}**\n\n{text}")
    except ImportError:
        await msg.edit_text("`lyrics-extractor not installed. Run: pip install lyrics-extractor`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")


async def _safe_extract(extractor, query):
    from zelretch.fns.tools import run_async
    return await run_async(extractor.get_lyrics)(query)

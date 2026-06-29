# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}imdb <keyword>`
    Search movie details from IMDB (via the imdbot inline bot).
"""

from __future__ import annotations

from plugins import eod, eor, zelretch_bot, zelretch_cmd


@zelretch_cmd(pattern=r"imdb\s+(.+)")
async def imdb(event):
    m = await event.reply("...")
    movie_name = event.matches[0].group(1).strip()
    if zelretch_bot is None:
        return await eod(m, "Bot client not ready.", time=5)
    try:
        results = await zelretch_bot.inline_query("imdbot", movie_name)
        if not results:
            return await eod(m, "No results found.", time=5)
        await results[0].click(event.chat.id)
        await m.delete()
    except Exception as er:
        return await eod(m, f"Could not search IMDB: `{er}`", time=10)

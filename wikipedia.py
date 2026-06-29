# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}wiki <search query>`
    Wikipedia search from Telegram.
"""

from __future__ import annotations

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"wiki\s+(.+)")
async def wiki(event):
    srch = event.matches[0].group(1).strip()
    msg = await event.reply(f"Searching `{srch}` on Wikipedia...")
    try:
        import wikipedia  # type: ignore
    except ImportError:
        return await eod(msg, "Install `wikipedia` to use this command.", time=10)
    try:
        summary = wikipedia.summary(srch)
        text = f"**Search Query:** {srch}\n\n**Results:** {summary}"
        await msg.edit(text)
    except wikipedia.exceptions.DisambiguationError as e:
        await msg.edit(f"Multiple matches: {', '.join(e.options[:5])}")
    except wikipedia.exceptions.PageError:
        await msg.edit(f"No Wikipedia page found for `{srch}`.")
    except Exception as err:
        await msg.edit(f"**ERROR**: {err}")

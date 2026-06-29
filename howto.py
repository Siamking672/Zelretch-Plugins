# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}howto <query>`
    Look up a quick how-to via the duckduckgo instant answer API.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"howto\s+(.+)")
async def howto(event):
    query = event.matches[0].group(1).strip()
    msg = await event.reply(f"Looking up `{query}`...")
    try:
        url = "https://api.duckduckgo.com/?q=" + urllib.parse.quote(query) + \
              "&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Zelretch/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data.get("AbstractText"):
            text = f"**{data['Heading']}**\n\n{data['AbstractText']}"
            if data.get("AbstractURL"):
                text += f"\n\n[Source]({data['AbstractURL']})"
            await msg.edit(text)
        else:
            related = data.get("RelatedTopics", [])[:5]
            if not related:
                return await eod(msg, f"No instant answer for `{query}`.", time=5)
            lines = []
            for item in related:
                if isinstance(item, dict) and item.get("Text"):
                    lines.append(f"• {item['Text'][:200]}")
            await msg.edit("**Related results:**\n\n" + "\n".join(lines))
    except Exception as er:
        await eod(msg, f"Lookup failed: `{er}`", time=10)

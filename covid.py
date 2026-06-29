# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}covid <country>`
    Show COVID-19 statistics for the given country (or global).
"""

from __future__ import annotations

import json
import urllib.request

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"covid(?:\s+(\S+))?$")
async def covid(event):
    country = (event.matches[0].group(1) if event.matches else "all").strip().lower()
    msg = await event.reply(f"Fetching COVID stats for `{country}`...")
    try:
        if country == "all":
            url = "https://disease.sh/v3/covid-19/all"
        else:
            url = f"https://disease.sh/v3/covid-19/countries/{country}"
        req = urllib.request.Request(url, headers={"User-Agent": "Zelretch/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if "message" in data:
            return await eod(msg, f"Country `{country}` not found.", time=5)
        text = (
            f"**COVID-19 statistics** - `{country}`\n\n"
            f"• Cases: `{data.get('cases', 0):,}`\n"
            f"• Today: `{data.get('todayCases', 0):,}`\n"
            f"• Deaths: `{data.get('deaths', 0):,}`\n"
            f"• Recovered: `{data.get('recovered', 0):,}`\n"
            f"• Active: `{data.get('active', 0):,}`\n"
            f"• Critical: `{data.get('critical', 0):,}`\n"
        )
        await msg.edit(text)
    except Exception as er:
        await eod(msg, f"Could not fetch stats: `{er}`", time=10)

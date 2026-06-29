# Zelretch Addons — Covid plugin
# Ported from UltroidAddons/covid.py
# Copyright (C) 2020-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}covid <country>`
    Show COVID-19 statistics for the given country.
"""

import requests

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"covid( (.*)|$)")
async def covid(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return await eor(message, "Give a country name to search for its Covid cases.")
    country = parts[1].strip().lower()
    msg = await message.reply_text(f"`Fetching COVID stats for {country.title()}…`")
    try:
        resp = requests.get(f"https://disease.sh/v3/covid-19/countries/{country}", timeout=15)
        data = resp.json()
        if "message" in data:
            return await msg.edit_text(f"`{data['message']}`")
        cases = data.get("cases", 0)
        active = data.get("active", 0)
        deaths = data.get("deaths", 0)
        recovered = data.get("recovered", 0)
        await msg.edit_text(
            f"**COVID-19 Stats — {data.get('country', country.title())}**\n\n"
            f"• **Cases:** `{cases:,}`\n"
            f"• **Active:** `{active:,}`\n"
            f"• **Deaths:** `{deaths:,}`\n"
            f"• **Recovered:** `{recovered:,}`"
        )
    except Exception as err:
        await msg.edit_text(f"**ERROR:** `{err}`")

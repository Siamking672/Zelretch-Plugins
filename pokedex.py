# Zelretch Addons — Pokedex lookup
# Ported from UltroidAddons/pokedex.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}pokedex <pokemon>`
    Show Pokemon stats.
"""

import requests

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"pokedex ?(.*)")
async def pokedex(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give a Pokemon name or ID.`")
    name = parts[1].strip().lower()
    msg = await message.reply_text(f"`Looking up {name}…`")
    try:
        resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}", timeout=15)
        if resp.status_code != 200:
            return await msg.edit_text(f"`Pokemon '{name}' not found.`")
        data = resp.json()
        types = ", ".join(t["type"]["name"] for t in data.get("types", []))
        stats = "\n".join(
            f"• **{s['stat']['name'].title()}:** `{s['base_stat']}`"
            for s in data.get("stats", [])
        )
        sprite = (data.get("sprites") or {}).get("front_default")
        text = (
            f"**#{data['id']} — {data['name'].title()}**\n\n"
            f"• **Type:** {types}\n"
            f"• **Height:** {data.get('height', 0) / 10} m\n"
            f"• **Weight:** {data.get('weight', 0) / 10} kg\n\n"
            f"**Stats:**\n{stats}"
        )
        if sprite:
            await client.send_photo(message.chat.id, sprite, caption=text)
            await msg.delete()
        else:
            await msg.edit_text(text)
    except Exception as err:
        await msg.edit_text(f"`{err}`")

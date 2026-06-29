# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}pokedex <pokemon name>`
    Show Pokémon details (via the PokéAPI).
"""

from __future__ import annotations

import json
import urllib.request

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"pokedex\s+(.+)")
async def pokedex(event):
    name = event.matches[0].group(1).strip().lower()
    msg = await event.reply(f"Looking up `{name}`...")
    try:
        req = urllib.request.Request(
            f"https://pokeapi.co/api/v2/pokemon/{name}",
            headers={"User-Agent": "Zelretch/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        types = ", ".join(t["type"]["name"] for t in data.get("types", []))
        abilities = ", ".join(a["ability"]["name"] for a in data.get("abilities", []))
        sprite = (data.get("sprites") or {}).get("front_default")
        text = (
            f"**{data['name'].title()}** (#{data['id']})\n\n"
            f"• Type: `{types}`\n"
            f"• Abilities: `{abilities}`\n"
            f"• Height: `{data.get('height', 0) / 10} m`\n"
            f"• Weight: `{data.get('weight', 0) / 10} kg`\n"
        )
        if sprite:
            await event.reply(text)
        else:
            await eor(msg, text)
        await msg.delete()
    except urllib.error.HTTPError:
        await eod(msg, f"Pokémon `{name}` not found.", time=5)
    except Exception as er:
        await eod(msg, f"Could not fetch Pokémon: `{er}`", time=10)

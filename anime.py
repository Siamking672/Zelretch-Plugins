# Zelretch Addons — Anime character search
# Ported from UltroidAddons/anime.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}character <name>`
    Fetch anime character details from Jikan (MyAnimeList).
"""

import jikanpy

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"character ?(.*)")
async def anime_char_search(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return await eor(message, "`Enter the name of a character.`", time=5)
    name = parts[1].strip()
    msg = await message.reply_text("`Searching…`")
    try:
        jikan = jikanpy.Jikan()
        s = jikan.search("character", name)
        if not s.get("results"):
            return await msg.edit_text("`Couldn't find character!`")
        mal_id = s["results"][0]["mal_id"]
        char = jikan.character(mal_id)
        text = f"**[{char['name']}]({char['url']})**"
        if char.get("name_kanji"):
            text += f"  [{char['name_kanji']}]\n"
        else:
            text += "\n"
        if char.get("nicknames"):
            text += f"\n**Nicknames:** `{', '.join(char['nicknames'])}`\n"
        about = (char.get("about") or "").split("\n", 1)[0].strip().replace("\n", " ")
        text += f"\n**About:** __{about[:600]}__"
        if char.get("image_url"):
            await client.send_photo(message.chat.id, char["image_url"], caption=text)
            await msg.delete()
        else:
            await msg.edit_text(text)
    except jikanpy.exceptions.APIException:
        await msg.edit_text("`Jikan API error — try again later.`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

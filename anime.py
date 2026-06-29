# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}character <character name>`
   Fetch anime character details (via Jikan / MyAnimeList).
"""

from __future__ import annotations

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"character\s+(.+)")
async def anime_char_search(event):
    xx = await event.reply("Searching...")
    char_name = event.matches[0].group(1).strip()
    try:
        import jikanpy  # type: ignore
    except ImportError:
        return await eod(xx, "Install `jikanpy` to use this command.", time=10)
    jikan = jikanpy.jikan.Jikan()
    try:
        s = jikan.search("character", char_name)
    except jikanpy.exceptions.APIException:
        return await eod(xx, "Couldn't find character!", time=5)
    a = s["results"][0]["mal_id"]
    char_json = jikan.character(a)
    pic = char_json["image_url"]
    msg = f"**[{char_json['name']}]({char_json['url']})**"
    if char_json.get("name_kanji") and char_json["name_kanji"] != "Japanese":
        msg += f" [{char_json['name_kanji']}]\n"
    else:
        msg += "\n"
    if char_json.get("nicknames"):
        msg += f"\n**Nicknames**: `{', '.join(char_json['nicknames'])}`\n"
    about = (char_json.get("about") or "").split("\n", 1)[0].strip().replace("\n", "")
    msg += f"\n**About**: __{about}__"
    try:
        await event.reply(msg, disable_web_page_preview=False)
    except Exception:
        await eor(xx, msg)
    await xx.delete()

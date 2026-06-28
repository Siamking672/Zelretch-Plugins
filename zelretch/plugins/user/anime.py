import os

from kurigram.errors import ChatSendMediaForbidden
from kurigram.types import Message

from zelretch.core import zelretch
from zelretch.functions.scraping import (
    get_airing_info,
    get_anilist_user_info,
    get_anime_info,
    get_character_info,
    get_filler_info,
    get_manga_info,
    get_watch_order,
)

from . import HelpMenu, on_message


@on_message("anime", allow_master=True)
async def anime(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me an anime name to search!")

    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Searching ...")
    caption, photo = await get_anime_info(query)

    try:
        await message.reply_photo(photo, caption=caption)
        await kaleido.delete()
    except ChatSendMediaForbidden:
        await kaleido.edit(caption, disable_web_page_preview=True)

    if os.path.exists(photo):
        os.remove(photo)


@on_message("manga", allow_master=True)
async def manga(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me a manga name to search!")

    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Searching ...")
    caption, photo = await get_manga_info(query)

    try:
        await message.reply_photo(photo, caption=caption)
        await kaleido.delete()
    except ChatSendMediaForbidden:
        await kaleido.edit(caption, disable_web_page_preview=True)

    if os.path.exists(photo):
        os.remove(photo)


@on_message("character", allow_master=True)
async def character(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me a character name to search!")

    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Searching ...")
    caption, photo = await get_character_info(query)

    try:
        await message.reply_photo(photo, caption=caption)
        await kaleido.delete()
    except ChatSendMediaForbidden:
        await kaleido.edit(caption, disable_web_page_preview=True)

    if os.path.exists(photo):
        os.remove(photo)


@on_message("airing", allow_master=True)
async def airing(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me an anime name to search!")

    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Searching ...")
    caption, photo = await get_airing_info(query)

    try:
        await message.reply_photo(photo, caption=caption)
        await kaleido.delete()
    except ChatSendMediaForbidden:
        await kaleido.edit(caption, disable_web_page_preview=True)

    if os.path.exists(photo):
        os.remove(photo)


@on_message(["anilistuser", "aniuser"], allow_master=True)
async def anilist_user(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me an anilist username to search!")

    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Searching ...")
    caption, photo = await get_anilist_user_info(query)

    try:
        await message.reply_photo(photo, caption=caption)
        await kaleido.delete()
    except ChatSendMediaForbidden:
        await kaleido.edit(caption, disable_web_page_preview=True)

    if os.path.exists(photo):
        os.remove(photo)


@on_message(["filler", "canon"], allow_master=True)
async def fillers(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me an anime name to search!")

    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Searching ...")

    caption = await get_filler_info(query)
    if caption == "":
        return await zelretch.delete(kaleido, "No results found!")

    await kaleido.edit(caption, disable_web_page_preview=True)


@on_message("watchorder", allow_master=True)
async def watch_order(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me an anime name to search!")

    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Searching ...")

    caption = await get_watch_order(query)
    if caption == "":
        return await zelretch.delete(kaleido, "No results found!")

    await kaleido.edit(caption, disable_web_page_preview=True)


HelpMenu("anime").add(
    "anime",
    "<name>",
    "Look up an anime on AniList and show its score, episodes, studio, genres, trailer, and synopsis.",
    "anime one piece",
).add(
    "manga",
    "<name>",
    "Look up a manga on AniList and show its score, chapters, volumes, status, and synopsis.",
    "manga one piece",
).add(
    "character",
    "<name>",
    "Look up a character on AniList and show their age, gender, birthday, and biography.",
    "character monkey d luffy",
).add(
    "airing",
    "<name>",
    "Show the next airing episode and countdown for an ongoing anime.",
    "airing one piece",
).add(
    "anilistuser",
    "<username>",
    "Fetch the AniList profile of a user, including anime and manga statistics.",
    "anilistuser meizhellboy",
    "Alias 'aniuser' can also be used.",
).add(
    "filler",
    "<name>",
    "List the filler and canon episodes of an anime so you can skip the non-canon arcs.",
    "filler one piece",
    "Alias 'canon' can also be used.",
).add(
    "watchorder",
    "<name>",
    "Show the recommended watch order for an anime franchise, including sequels, movies, and OVAs.",
    "watchorder one piece",
).info(
    "AniList-powered anime, manga, and character lookups plus filler guides and watch orders."
).done()

from lyricsgenius import Genius
from pyrogram.errors import MessageTooLong
from pyrogram.types import Message

from zelretch.core import ENV
from zelretch.functions.paste import post_to_telegraph

from . import HelpMenu, Symbols, db, zelretch, on_message


@on_message("lyrics", allow_master=True)
async def getlyrics(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Provide a song name to fetch lyrics.")

    api = await db.get_env(ENV.lyrics_api)
    if not api:
        return await zelretch.delete(message, "Lyrics API not found.")

    query = await zelretch.input(message)
    if "-" in query:
        artist, song = query.split("-")
    else:
        artist, song = "", query

    hell = await zelretch.edit(message, f"🔎 __𝖫𝗒𝗋𝗂𝖼𝗌 𝖲𝗈𝗇𝗀__ `{query}`...")

    genius = Genius(
        api,
        verbose=False,
        remove_section_headers=True,
        skip_non_songs=True,
        excluded_terms=["(Remix)", "(Live)"],
    )

    song = genius.search_song(song, artist)
    if not song:
        return await zelretch.delete(hell, "No results found.")

    title = song.full_title
    image = song.song_art_image_url
    artist = song.artist
    lyrics = song.lyrics

    outStr = f"<b>{Symbols.anchor} Title:</b> <code>{title}</code>\n<b>{Symbols.anchor} Artist:</b> <code>{artist}</code>\n\n<code>{lyrics}</code>"
    try:
        await hell.edit(outStr, disable_web_page_preview=True)
    except MessageTooLong:
        content = f"<img src='{image}'/>\n\n{outStr}"
        url = post_to_telegraph(title, content)
        await hell.edit(
            f"**{Symbols.anchor} Title:** `{title}`\n**{Symbols.anchor} Artist:** `{artist}`\n\n**{Symbols.anchor} Lyrics:** [Click Here]({url})",
            disable_web_page_preview=True,
        )


HelpMenu("lyrics").add(
    "lyrics",
    "<song name>",
    "Get the lyrics of the given song! Give artist name after - to get accurate results.",
    "lyrics believer - imagine dragons",
    "Need to setup Lyrics Api key from https://genius.com/developers",
).info(
    "Lyrics lookup"
).done()

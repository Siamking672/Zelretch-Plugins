from lyricsgenius import Genius
from kurigram.errors import MessageTooLong
from kurigram.types import Message

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

    kaleido = await zelretch.edit(message, f"🔎 __𝖫𝗒𝗋𝗂𝖼𝗌 𝖲𝗈𝗇𝗀__ `{query}`...")

    genius = Genius(
        api,
        verbose=False,
        remove_section_headers=True,
        skip_non_songs=True,
        excluded_terms=["(Remix)", "(Live)"],
    )

    song = genius.search_song(song, artist)
    if not song:
        return await zelretch.delete(kaleido, "No results found.")

    title = song.full_title
    image = song.song_art_image_url
    artist = song.artist
    lyrics = song.lyrics

    outStr = f"<b>{Symbols.anchor} Title:</b> <code>{title}</code>\n<b>{Symbols.anchor} Artist:</b> <code>{artist}</code>\n\n<code>{lyrics}</code>"
    try:
        await kaleido.edit(outStr, disable_web_page_preview=True)
    except MessageTooLong:
        content = f"<img src='{image}'/>\n\n{outStr}"
        url = post_to_telegraph(title, content)
        await kaleido.edit(
            f"**{Symbols.anchor} Title:** `{title}`\n**{Symbols.anchor} Artist:** `{artist}`\n\n**{Symbols.anchor} Lyrics:** [Click Here]({url})",
            disable_web_page_preview=True,
        )


HelpMenu("lyrics").add(
    "lyrics",
    "<song name> - <artist name (optional)>",
    "Fetch the full lyrics of a song from Genius. Append the artist name after a dash for more accurate matching.",
    "lyrics believer - imagine dragons",
    "Requires the LYRICS_API variable. Get a free API key from https://genius.com/developers.",
).info(
    "Song lyrics lookup powered by the Genius API."
).done()

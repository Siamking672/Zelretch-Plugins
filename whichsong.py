# Zelretch Addons — Which song (Shazam-based)
# Ported from UltroidAddons/whichsong.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}whichsong <reply to audio>`
    Alias for `{i}findsong` — identify a song.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="whichsong$")
async def whichsong(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.audio or reply.voice):
        return await eor(message, "`Reply to an audio file.`")
    msg = await message.reply_text("`Identifying song…`")
    try:
        from shazamio import Shazam
        path = await reply.download(in_memory=True)
        path.seek(0)
        shazam = Shazam()
        out = await shazam.recognize(path.read())
        track = out.get("track", {})
        if not track:
            return await msg.edit_text("`Could not identify the song.`")
        title = track.get("title", "?")
        subtitle = track.get("subtitle", "")
        await msg.edit_text(f"🎵 **{title}** — {subtitle}")
    except ImportError:
        await msg.edit_text("`shazamio not installed. Run: pip install shazamio`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

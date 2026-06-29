# Zelretch Addons — Find song (audio fingerprint)
# Ported from UltroidAddons/findsong.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}findsong <reply to audio>`
    Identify a song using Shazam (best-effort).
"""

import io

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="findsong$")
async def find_song(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.audio or reply.voice):
        return await eor(message, "`Reply to an audio file.`")
    msg = await message.reply_text("`Identifying song…`")
    try:
        from shazamio import Shazam
        path = await reply.download(in_memory=True)
        path.seek(0)
        shazam = Shazam()
        result = await shazam.recognize(path.read())
        track = result.get("track")
        if not track:
            return await msg.edit_text("`Could not identify the song.`")
        title = track.get("title", "?")
        subtitle = track.get("subtitle", "")
        await msg.edit_text(f"🎵 **Identified:** {title} — {subtitle}")
    except ImportError:
        await msg.edit_text("`shazamio not installed. Run: pip install shazamio`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

# Zelretch Addons — Speech tools (text-to-speech)
# Ported from UltroidAddons/speechtool.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}tts <text>`
    Convert text to speech (MP3 voice note).
"""

import io

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"tts ?(.*)")
async def tts(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    text = parts[1].strip()
    msg = await message.reply_text("`Generating speech…`")
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=text, lang="en").write_to_fp(buf)
        buf.seek(0)
        buf.name = "tts.mp3"
        await client.send_voice(message.chat.id, buf)
        await msg.delete()
    except ImportError:
        await msg.edit_text("`gtts not installed. Run: pip install gtts`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

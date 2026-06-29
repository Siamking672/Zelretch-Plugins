# Zelretch Addons — Spell checker
# Ported from UltroidAddons/spellcheck.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}spell <word>`
    Check the spelling of a word.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"spell ?(.*)")
async def spell(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give a word to check.`")
    word = parts[1].strip()
    try:
        from textblob import TextBlob
        blob = TextBlob(word)
        corrected = str(blob.correct())
        if corrected.lower() == word.lower():
            await eor(message, f"✓ `{word}` is spelled correctly.")
        else:
            await eor(message, f"Did you mean: `{corrected}`?")
    except ImportError:
        await eor(message, "`textblob is not installed. Run: pip install textblob`")
    except Exception as err:
        await eor(message, f"`{err}`")

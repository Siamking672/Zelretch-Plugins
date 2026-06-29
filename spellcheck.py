# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}spellcheck <word>`
    Check the spelling of a word (uses ``textblob``).
"""

from __future__ import annotations

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"spellcheck\s+(\S+)")
async def spellcheck(event):
    word = event.matches[0].group(1)
    try:
        from textblob import TextBlob  # type: ignore
        b = TextBlob(word)
        corrected = b.correct()
        if str(corrected).lower() == word.lower():
            await eor(event, f"✅ `{word}` looks correct.")
        else:
            await eor(event, f"❓ Did you mean `{corrected}`?")
    except ImportError:
        await eod(event, "Install `textblob` to use this command.", time=10)

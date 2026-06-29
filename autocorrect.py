# Zelretch Addons — Autocorrect
# Ported from UltroidAddons/autocorrect.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}autocorrect <text>`
    Auto-correct spelling of an entire sentence.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"autocorrect ?(.*)")
async def autocorrect(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give a sentence.`")
    try:
        from textblob import TextBlob
        corrected = str(TextBlob(parts[1]).correct())
        await eor(message, f"**Original:** `{parts[1]}`\n**Corrected:** `{corrected}`")
    except ImportError:
        await eor(message, "`textblob not installed. Run: pip install textblob`")
    except Exception as err:
        await eor(message, f"`{err}`")

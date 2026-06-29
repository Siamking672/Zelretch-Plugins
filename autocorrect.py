# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}autocorrect <text>`
    Auto-correct text (uses ``textblob`` if installed).
"""

from __future__ import annotations

from plugins import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"autocorrect\s+(.+)")
async def autocorrect(event):
    text = event.matches[0].group(1)
    try:
        from textblob import TextBlob  # type: ignore
        corrected = TextBlob(text).correct()
        await eor(event, f"**Original:** {text}\n\n**Corrected:** {corrected}")
    except ImportError:
        await eod(event, "Install `textblob` to use this command.", time=10)

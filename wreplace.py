# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""
✘ Commands Available -

• `{i}wreplace <text>`
    Replace whitespace with underscores (useful for filename-safe strings).
"""

from __future__ import annotations

from plugins import eor, zelretch_cmd


@zelretch_cmd(pattern=r"wreplace\s+(.+)")
async def wreplace(event):
    text = event.matches[0].group(1)
    await eor(event, text.replace(" ", "_"))

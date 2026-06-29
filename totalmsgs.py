# Zelretch Addons — Total message count
# Ported from UltroidAddons/totalmsgs.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}totalmsgs`
    Count messages in the current chat (best-effort).
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="totalmsgs$")
async def total_msgs(client, message):
    msg = await message.reply_text("`Counting messages…`")
    try:
        count = await client.search_messages_count(message.chat.id)
        await msg.edit_text(f"**Total messages in this chat:** `{count:,}`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

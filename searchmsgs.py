# Zelretch Addons — Search messages
# Ported from UltroidAddons/searchmsgs.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}search <query>`
    Search messages in the current chat.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"search ?(.*)")
async def search_msgs(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give a search query.`")
    query = parts[1].strip()
    msg = await message.reply_text(f"`Searching for '{query}'…`")
    try:
        found = []
        async for m in client.search_messages(message.chat.id, query=query, limit=5):
            if m.text:
                snippet = m.text[:120].replace("\n", " ")
                found.append(f"• [{m.link}]({m.link}) — _{snippet}_")
        if found:
            await msg.edit_text("**Search results:**\n\n" + "\n".join(found))
        else:
            await msg.edit_text("`No messages found.`")
    except Exception as err:
        await msg.edit_text(f"`{err}`")

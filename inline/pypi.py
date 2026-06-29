# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/UltroidAddons/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Inline pypi search - respond to inline queries with PyPI package results."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from plugins import LOGS, zelretch_bot


async def pypi_inline(client, inline_query):
    q = inline_query.query.strip()
    if not q:
        return
    try:
        url = "https://pypi.org/simple/" + urllib.parse.quote(q) + "/"
        # The simple API returns HTML, so fall back to the JSON API.
        url = f"https://pypi.org/pypi/{urllib.parse.quote(q)}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "Zelretch/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        info = data.get("info", {})
        if not info:
            return
        from kurigram.types import (  # type: ignore
            InlineQueryResultArticle,
            InputTextMessageContent,
        )
        await client.answer_inline_query(
            inline_query.id,
            results=[
                InlineQueryResultArticle(
                    id=f"pypi-{q}",
                    title=f"{info.get('name', q)} {info.get('version', '')}",
                    description=info.get("summary", "")[:200],
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"**{info['name']}** v{info.get('version', '?')}\n\n"
                            f"{info.get('summary', '')}\n\n"
                            f"[PyPI]({info.get('package_url', '')})"
                        ),
                    ),
                )
            ],
        )
    except Exception as er:
        LOGS.info(f"pypi inline failed: {er}")


if zelretch_bot is not None:
    try:
        from kurigram import filters  # type: ignore
        zelretch_bot.add_inline_handler(pypi_inline, None)
    except Exception as er:
        LOGS.info(f"pypi inline handler not attached: {er}")

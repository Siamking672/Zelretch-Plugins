# Zelretch Addons — Inline PyPI search
# Ported from UltroidAddons/inline/pypi.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""Inline query: search PyPI for a package."""

import requests

from zelretch.core.decorators import in_ring

try:
    from kurigram.types import (
        InlineQueryResultArticle,
        InputTextMessageContent,
    )
    KURIGRAM_AVAILABLE = True
except ImportError:  # pragma: no cover
    KURIGRAM_AVAILABLE = False


@in_ring
async def pypi_inline(client, inline_query):
    if not inline_query.query:
        return
    if not inline_query.query.startswith("pypi "):
        return
    query = inline_query.query.split(maxsplit=1)[1].strip()
    try:
        resp = requests.get(
            "https://pypi.org/pypi/" + query + "/json",
            timeout=10,
        )
        if resp.status_code != 200:
            return
        data = resp.json()
        info = data.get("info", {})
        if not KURIGRAM_AVAILABLE:
            return
        await client.answer_inline_query(
            inline_query.id,
            results=[
                InlineQueryResultArticle(
                    id=str(info.get("name", query)),
                    title=info.get("name", "?"),
                    description=info.get("summary", ""),
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"**{info.get('name')}** v{info.get('version')}\n\n"
                            f"{info.get('summary', '')}\n\n"
                            f"[PyPI]({info.get('package_url')})"
                        ),
                    ),
                )
            ],
        )
    except Exception:
        pass

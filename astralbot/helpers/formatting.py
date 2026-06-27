"""Formatting helpers — HTML / Markdown rendering for plugin output."""

from __future__ import annotations

import html
import re


def escape_html(text: str) -> str:
    return html.escape(str(text), quote=False)


def mention_user(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{escape_html(name)}</a>'


def code_block(text: str, language: str = "") -> str:
    return f"```{language}\n{text}\n```"


def inline_code(text: str) -> str:
    return f"`{text}`"


def bold(text: str) -> str:
    return f"**{text}**"


def italic(text: str) -> str:
    return f"__{text}__"


def strike(text: str) -> str:
    return f"~~{text}~~"


def link(text: str, url: str) -> str:
    return f"[{text}]({url})"


def strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text)


def truncate(text: str, max_len: int = 4096, suffix: str = "...") -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def chunk_text(text: str, max_len: int = 4096) -> list[str]:
    """Split a long string into chunks that fit Telegram's message limit."""
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to break on a newline
        cut = text.rfind("\n", 0, max_len)
        if cut == -1:
            cut = max_len
        chunks.append(text[:cut])
        text = text[cut:].lstrip()
    return chunks

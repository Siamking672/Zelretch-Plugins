"""Paste service helpers — upload text to a paste service."""

from __future__ import annotations

from astralbot.helpers.net import fetch_text, post_json


async def paste_to_spacebin(text: str) -> str | None:
    """Upload to spaceb.in. Returns the URL or None on failure."""
    try:
        result = await post_json(
            "https://spaceb.in/api/v1/documents",
            {"content": text, "extension": "txt"},
        )
        if isinstance(result, dict) and "payload" in result:
            return f"https://spaceb.in/{result['payload']['id']}"
    except Exception:
        pass
    return None


async def paste_to_nektobin(text: str) -> str | None:
    """Upload to nektobin (a hastebin-style service)."""
    try:
        result = await post_json(
            "https://nekobin.com/api/documents",
            {"content": text},
        )
        if isinstance(result, dict) and "result" in result:
            return f"https://nekobin.com/{result['result']['key']}"
    except Exception:
        pass
    return None


async def paste(text: str) -> str:
    """Try multiple paste services. Returns the first successful URL."""
    for fn in (paste_to_nektobin, paste_to_spacebin):
        url = await fn(text)
        if url:
            return url
    return "(paste upload failed)"

"""HTTP fetch helpers."""

from __future__ import annotations

import json
from typing import Any, Optional

try:
    import aiohttp
    _HAS_AIOHTTP = True
except ImportError:
    _HAS_AIOHTTP = False

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


async def fetch_json(url: str, *, headers: Optional[dict] = None, timeout: int = 30) -> Any:
    """Async GET that returns parsed JSON."""
    if _HAS_AIOHTTP:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                return await resp.json()
    # Fall back to requests in a thread
    if not _HAS_REQUESTS:
        raise RuntimeError("Neither aiohttp nor requests is installed.")
    import asyncio
    loop = asyncio.get_event_loop()
    def _sync():
        r = requests.get(url, headers=headers, timeout=timeout)
        return r.json()
    return await loop.run_in_executor(None, _sync)


async def fetch_text(url: str, *, headers: Optional[dict] = None, timeout: int = 30) -> str:
    if _HAS_AIOHTTP:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                return await resp.text()
    if not _HAS_REQUESTS:
        raise RuntimeError("Neither aiohttp nor requests is installed.")
    import asyncio
    loop = asyncio.get_event_loop()
    def _sync():
        r = requests.get(url, headers=headers, timeout=timeout)
        return r.text
    return await loop.run_in_executor(None, _sync)


async def fetch_bytes(url: str, *, headers: Optional[dict] = None, timeout: int = 60) -> bytes | None:
    """Fetch a URL and return raw bytes."""
    if _HAS_AIOHTTP:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status != 200:
                    return None
                return await resp.read()
    if not _HAS_REQUESTS:
        raise RuntimeError("Neither aiohttp nor requests is installed.")
    import asyncio
    loop = asyncio.get_event_loop()
    def _sync():
        r = requests.get(url, headers=headers, timeout=timeout, stream=True)
        if r.status_code != 200:
            return None
        return r.content
    return await loop.run_in_executor(None, _sync)


async def post_json(url: str, body: dict, *, headers: Optional[dict] = None, timeout: int = 30) -> Any:
    if _HAS_AIOHTTP:
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        async with aiohttp.ClientSession(headers=h) as session:
            async with session.post(url, data=json.dumps(body), timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                return await resp.json()
    if not _HAS_REQUESTS:
        raise RuntimeError("Neither aiohttp nor requests is installed.")
    import asyncio
    loop = asyncio.get_event_loop()
    def _sync():
        r = requests.post(url, json=body, headers=headers, timeout=timeout)
        return r.json()
    return await loop.run_in_executor(None, _sync)

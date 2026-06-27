"""Media download / upload helpers."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogram import Client
    from pyrogram.types import Message


async def download_media(
    client: "Client",
    message: "Message",
    dest_dir: str | Path = "userdata/downloads",
    progress: bool = False,
) -> Path | None:
    """Download media attached to a message. Returns the saved file path."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        path = await client.download_media(
            message,
            file_name=str(dest_dir),
            in_memory=False,
            progress=None if not progress else None,
        )
        return Path(path) if path else None
    except Exception:
        return None


async def upload_file(
    client: "Client",
    chat_id: int | str,
    file_path: str | Path,
    caption: str | None = None,
    as_document: bool = True,
) -> "Message | None":
    """Upload a file to a chat. as_document=True sends as a doc (no re-encoding)."""
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    try:
        if as_document:
            return await client.send_document(chat_id, str(file_path), caption=caption)
        # Otherwise let Pyrogram pick the type by mime
        ext = file_path.suffix.lower()
        if ext in (".jpg", ".jpeg", ".png", ".webp"):
            return await client.send_photo(chat_id, str(file_path), caption=caption)
        if ext in (".mp4", ".gif", ".webm"):
            return await client.send_video(chat_id, str(file_path), caption=caption)
        if ext in (".mp3", ".ogg", ".m4a", ".wav"):
            return await client.send_audio(chat_id, str(file_path), caption=caption)
        return await client.send_document(chat_id, str(file_path), caption=caption)
    except Exception:
        return None


def human_size(num_bytes: int) -> str:
    """Format bytes as a human-readable string."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

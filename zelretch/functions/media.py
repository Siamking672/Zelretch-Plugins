"""Media helpers for sticker and group plugins.

Only the functions still used by remaining plugins are kept here:

* ``upload_media``       — used by ``sticker`` plugin.
* ``get_media_from_id``  — used by ``sticker`` plugin.
* ``get_media_fileid``   — used by ``groups`` plugin.

The ``get_metedata`` function (media-type metadata formatter) was only
used by the now-deleted ``media`` plugin and has been removed.
"""

import os

from kurigram import Client
from kurigram.file_id import FileId
from kurigram.raw.functions.messages import UploadMedia
from kurigram.raw.types import (
    DocumentAttributeFilename,
    InputDocument,
    InputMediaUploadedDocument,
)
from kurigram.types import Message


async def upload_media(client: Client, chat_id: int, file: str) -> InputDocument:
    media = await client.invoke(
        UploadMedia(
            peer=(await client.resolve_peer(chat_id)),
            media=InputMediaUploadedDocument(
                file=(await client.save_file(file)),
                mime_type=client.guess_mime_type(file) or "application/zip",
                attributes=[
                    DocumentAttributeFilename(file_name=os.path.basename(file))
                ],
                force_file=True,
            ),
        ),
    )

    return InputDocument(
        id=media.document.id,
        access_hash=media.document.access_hash,
        file_reference=media.document.file_reference,
    )


async def get_media_from_id(file_id: str) -> InputDocument:
    file = FileId.decode(file_id)

    return InputDocument(
        id=file.media_id,
        access_hash=file.access_hash,
        file_reference=file.file_reference,
    )


async def get_media_fileid(message: Message) -> str | None:
    file_id = None
    if message.photo:
        file_id = message.photo.file_id
    elif message.animation:
        file_id = message.animation.file_id
    elif message.audio:
        file_id = message.audio.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.sticker:
        file_id = message.sticker.file_id
    elif message.video_note:
        file_id = message.video_note.file_id
    elif message.voice:
        file_id = message.voice.file_id
    return file_id

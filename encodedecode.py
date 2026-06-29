# Zelretch Addons — Encode / Decode (base64, hex, url)
# Ported from UltroidAddons/encodedecode.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}encode <text>`
    Base64-encode text.

• `{i}decode <base64>`
    Base64-decode text.

• `{i}hexencode <text>`
    Hex-encode text.

• `{i}hexdecode <hex>`
    Hex-decode text.

• `{i}urlencode <text>`
    URL-encode text.

• `{i}urldecode <text>`
    URL-decode text.
"""

import base64
from urllib.parse import quote, unquote

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"encode ?(.*)")
async def encode_b64(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text to encode.`")
    encoded = base64.b64encode(parts[1].encode()).decode()
    await eor(message, f"`{encoded}`")


@zelretch_cmd(pattern=r"decode ?(.*)")
async def decode_b64(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give base64 to decode.`")
    try:
        decoded = base64.b64decode(parts[1].strip()).decode(errors="replace")
        await eor(message, f"`{decoded}`")
    except Exception as err:
        await eor(message, f"`{err}`")


@zelretch_cmd(pattern=r"hexencode ?(.*)")
async def hex_encode(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    await eor(message, f"`{parts[1].encode().hex()}`")


@zelretch_cmd(pattern=r"hexdecode ?(.*)")
async def hex_decode(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give hex string.`")
    try:
        await eor(message, f"`{bytes.fromhex(parts[1].strip()).decode(errors='replace')}`")
    except Exception as err:
        await eor(message, f"`{err}`")


@zelretch_cmd(pattern=r"urlencode ?(.*)")
async def url_encode(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    await eor(message, f"`{quote(parts[1])}`")


@zelretch_cmd(pattern=r"urldecode ?(.*)")
async def url_decode(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    await eor(message, f"`{unquote(parts[1])}`")

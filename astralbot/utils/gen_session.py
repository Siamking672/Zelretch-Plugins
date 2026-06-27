"""
Generate a Pyrogram StringSession for AstralBot.

Usage::

    python -m astralbot.utils.gen_session

You'll be prompted for your API_ID and API_HASH (from https://my.telegram.org/apps),
then for your phone number, login code, and (if enabled) 2FA password. The
session string is printed to stdout — copy it into your .env file as
STRING_SESSION.
"""

from __future__ import annotations

import asyncio
import os
import sys


async def main() -> None:
    try:
        from pyrogram import Client
    except ImportError:
        print("Pyrogram is not installed. Run: pip install pyrogram tgcrypto", file=sys.stderr)
        sys.exit(1)

    print("=== AstralBot Session Generator ===\n")

    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    if not api_id or not api_hash:
        api_id = input("Enter API_ID: ").strip()
        api_hash = input("Enter API_HASH: ").strip()
    if not api_id or not api_hash:
        print("API_ID and API_HASH are required.", file=sys.stderr)
        sys.exit(1)

    try:
        api_id_int = int(api_id)
    except ValueError:
        print("API_ID must be an integer.", file=sys.stderr)
        sys.exit(1)

    async with Client(
        name=":memory:",
        api_id=api_id_int,
        api_hash=api_hash,
        in_memory=True,
    ) as app:
        session_string = await app.export_session_string()
        me = await app.get_me()
        print("\n" + "=" * 60)
        print("✅ Session generated successfully!")
        print(f"   Account: @{me.username} (id={me.id})")
        print("=" * 60)
        print("\nAdd this line to your .env file:\n")
        print(f"STRING_SESSION={session_string}")
        print("\n⚠️  KEEP THIS SECRET — anyone with this string can control your account.")


if __name__ == "__main__":
    asyncio.run(main())

"""Interactive userbot-session creation.

Implements a three-step OTP flow over HTTP so the wizard can create a
Pyrogram session string from inside the browser:

  1. POST /session/start   -> sends OTP, returns a temporary session id
  2. POST /session/verify  -> submits OTP, returns session string OR
                              signals that a 2FA password is required
  3. POST /session/password-> submits 2FA password, returns session string

A single :class:`SessionBuilder` instance is held in a module-level
registry keyed by ``session_id`` so the underlying Pyrogram client
survives between requests. Builders auto-expire after 5 minutes of
inactivity.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from kurigram import Client
from kurigram.errors import SessionPasswordNeeded

from .validators import validate_phone

_TTL_SECONDS = 5 * 60


@dataclass
class SessionBuilder:
    """Holds an in-flight Pyrogram client between OTP requests."""

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    api_id: int = 0
    api_hash: str = ""
    phone: str = ""
    phone_code_hash: str = ""
    client: Optional[Client] = None
    created_at: float = field(default_factory=time.time)
    last_touched: float = field(default_factory=time.time)
    loop: Optional[asyncio.AbstractEventLoop] = None

    def touch(self) -> None:
        self.last_touched = time.time()


# Module-level registry. The wizard process is single-user so a plain
# dict is sufficient; no need for a real session store.
_builders: dict[str, SessionBuilder] = {}


def _purge_expired() -> None:
    now = time.time()
    expired = [sid for sid, b in _builders.items() if now - b.last_touched > _TTL_SECONDS]
    for sid in expired:
        builder = _builders.pop(sid, None)
        if builder and builder.client and builder.loop:
            try:
                builder.loop.run_until_complete(builder.client.disconnect())
            except Exception:
                pass
            if not builder.loop.is_closed():
                try:
                    builder.loop.close()
                except Exception:
                    pass


def _get_builder(session_id: str) -> Optional[SessionBuilder]:
    _purge_expired()
    return _builders.get(session_id)


def start_session_sync(api_id: int, api_hash: str, phone: str) -> tuple[bool, str, Optional[str]]:
    """Send the OTP code. Returns ``(ok, message, session_id)``.

    On success, ``session_id`` is a token the client must pass back on
    subsequent requests.
    """
    try:
        api_id = int(api_id)
    except (TypeError, ValueError):
        return False, "API_ID must be a valid integer.", None

    ok, msg = validate_phone(phone)
    if not ok:
        return False, msg, None

    if not api_id or not api_hash:
        return False, "API_ID and API_HASH are required to create a session.", None

    builder = SessionBuilder(api_id=api_id, api_hash=api_hash, phone=phone)

    # Create a dedicated event loop on a worker thread so we don't bind
    # to the Flask request thread.
    loop = asyncio.new_event_loop()

    async def _send():
        client = Client(
            name=f"zelretch_deploy_{builder.session_id[:8]}",
            api_id=api_id,
            api_hash=api_hash,
            in_memory=True,
        )
        await client.connect()
        try:
            sent = await client.send_code(phone)
            builder.client = client
            builder.phone_code_hash = sent.phone_code_hash
        except Exception as exc:
            await client.disconnect()
            raise

    try:
        loop.run_until_complete(_send())
    except Exception as exc:
        loop.close()
        return False, f"Failed to send OTP: {exc}", None

    builder.loop = loop
    _builders[builder.session_id] = builder
    return True, "OTP sent. Check your Telegram app.", builder.session_id


def verify_otp_sync(session_id: str, otp: str) -> tuple[bool, str, Optional[str], bool]:
    """Submit the OTP.

    Returns ``(ok, message, session_string, needs_password)``.
    """
    builder = _get_builder(session_id)
    if not builder or not builder.client:
        return False, "Session expired or invalid. Please restart the OTP flow.", None, False

    builder.touch()
    otp = (otp or "").replace(" ", "").strip()
    if not otp.isdigit():
        return False, "OTP must be digits only.", None, False

    loop = builder.loop

    async def _verify():
        try:
            await builder.client.sign_in(builder.phone, builder.phone_code_hash, otp)
        except SessionPasswordNeeded:
            return None, True  # cloud password required
        return await builder.client.export_session_string(), False

    try:
        session_string, needs_password = loop.run_until_complete(_verify())
    except Exception as exc:
        _cleanup(builder)
        return False, f"OTP verification failed: {exc}", None, False

    if needs_password:
        return True, "Two-step verification password required.", None, True

    if not session_string:
        _cleanup(builder)
        return False, "Failed to export session string.", None, False

    _cleanup(builder)
    return True, "Session created successfully.", session_string, False


def submit_password_sync(session_id: str, password: str) -> tuple[bool, str, Optional[str]]:
    """Submit the 2FA password and finalize the session."""
    builder = _get_builder(session_id)
    if not builder or not builder.client:
        return False, "Session expired or invalid. Please restart the OTP flow.", None

    builder.touch()
    if not password:
        return False, "Password is required.", None

    loop = builder.loop

    async def _password():
        await builder.client.check_password(password)
        return await builder.client.export_session_string()

    try:
        session_string = loop.run_until_complete(_password())
    except Exception as exc:
        _cleanup(builder)
        return False, f"Password verification failed: {exc}", None

    if not session_string:
        _cleanup(builder)
        return False, "Failed to export session string.", None

    _cleanup(builder)
    return True, "Session created successfully.", session_string


def _cleanup(builder: SessionBuilder) -> None:
    _builders.pop(builder.session_id, None)
    loop = builder.loop
    if builder.client and loop and not loop.is_closed():
        try:
            loop.run_until_complete(builder.client.disconnect())
        except Exception:
            pass
    if loop and not loop.is_closed():
        try:
            loop.close()
        except Exception:
            pass

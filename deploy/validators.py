"""Form-field validation for the deployment wizard.

All validators return ``(is_valid: bool, errors: dict[str, str], cleaned: dict[str, str])``.
The ``errors`` dict maps field name -> user-facing message; empty when valid.
The ``cleaned`` dict contains the canonicalised values; empty when invalid.
"""

from __future__ import annotations

import re
from typing import Any

# Bot token format: ``<bot_id>:<35-char HMAC>``.
_BOT_TOKEN = re.compile(r"^[1-9][0-9]{4,12}:[A-Za-z0-9_-]{30,40}$")
# Telegram API_ID is a positive integer (typically 6-8 digits).
_API_ID = re.compile(r"^[1-9][0-9]{3,11}$")
# Telegram user/chat IDs are non-zero integers (can be negative for groups).
_TG_ID = re.compile(r"^-?[1-9][0-9]{3,12}$")
# GitHub ``owner/repo`` shorthand; allow full URLs too.
_REPO = re.compile(r"^(?:https?://github\.com/)?([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+?)(?:\.git)?/?$")
# MongoDB URI: ``mongodb://...`` or ``mongodb+srv://...``.
_MONGO = re.compile(r"^mongodb(?:\+srv)?://[^\s]+$")
# Phone numbers: leading ``+`` then 7-15 digits.
_PHONE = re.compile(r"^\+[1-9][0-9]{6,14}$")


def _err(field: str, msg: str) -> tuple[bool, dict[str, str], dict[str, Any]]:
    return False, {field: msg}, {}


def validate_required(form: Any) -> tuple[bool, dict[str, str], dict[str, Any]]:
    """Validate the core deployment variables (step 1 of the wizard)."""
    errors: dict[str, str] = {}
    cleaned: dict[str, str] = {}

    def get(key: str) -> str:
        v = form.get(key, "").strip()
        return v

    # API_ID
    api_id = get("API_ID")
    if not api_id:
        errors["API_ID"] = "API_ID is required."
    elif not _API_ID.match(api_id):
        errors["API_ID"] = "API_ID must be a positive integer from my.telegram.org."
    else:
        cleaned["API_ID"] = api_id

    # API_HASH
    api_hash = get("API_HASH")
    if not api_hash:
        errors["API_HASH"] = "API_HASH is required."
    elif len(api_hash) < 16:
        errors["API_HASH"] = "API_HASH looks too short (expected ~32 hex chars)."
    else:
        cleaned["API_HASH"] = api_hash

    # BOT_TOKEN
    bot_token = get("BOT_TOKEN")
    if not bot_token:
        errors["BOT_TOKEN"] = "BOT_TOKEN is required."
    elif not _BOT_TOKEN.match(bot_token):
        errors["BOT_TOKEN"] = "BOT_TOKEN format is invalid. Get it from @BotFather."
    else:
        cleaned["BOT_TOKEN"] = bot_token

    # OWNER_ID
    owner_id = get("OWNER_ID")
    if not owner_id:
        errors["OWNER_ID"] = "OWNER_ID is required."
    elif not _TG_ID.match(owner_id):
        errors["OWNER_ID"] = "OWNER_ID must be your numeric Telegram user ID."
    else:
        cleaned["OWNER_ID"] = owner_id

    # LOGGER_ID
    logger_id = get("LOGGER_ID")
    if not logger_id:
        errors["LOGGER_ID"] = "LOGGER_ID is required."
    elif not _TG_ID.match(logger_id):
        errors["LOGGER_ID"] = "LOGGER_ID must be a numeric chat ID (negative for groups)."
    else:
        cleaned["LOGGER_ID"] = logger_id

    # DATABASE_URL
    db_url = get("DATABASE_URL")
    if not db_url:
        errors["DATABASE_URL"] = "DATABASE_URL is required."
    elif not _MONGO.match(db_url):
        errors["DATABASE_URL"] = "DATABASE_URL must start with mongodb:// or mongodb+srv://"
    else:
        cleaned["DATABASE_URL"] = db_url

    # DATABASE_NAME (optional, default Zelretch)
    db_name = get("DATABASE_NAME") or "Zelretch"
    if not re.match(r"^[A-Za-z0-9_\-]{1,64}$", db_name):
        errors["DATABASE_NAME"] = "DATABASE_NAME may only contain letters, digits, _ or -."
    else:
        cleaned["DATABASE_NAME"] = db_name

    # HANDLERS (optional)
    handlers = get("HANDLERS") or ". ! ?"
    cleaned["HANDLERS"] = handlers

    # PLUGINS_REPO (optional, default Siamking672/Zelretch-Plugins)
    plugins_repo = get("PLUGINS_REPO") or "Siamking672/Zelretch-Plugins"
    m = _REPO.match(plugins_repo)
    if not m:
        errors["PLUGINS_REPO"] = "PLUGINS_REPO must be 'owner/repo' or a GitHub URL."
    else:
        cleaned["PLUGINS_REPO"] = f"{m.group(1)}/{m.group(2)}"

    # PLUGINS_BRANCH (optional)
    plugins_branch = get("PLUGINS_BRANCH") or "main"
    if not re.match(r"^[A-Za-z0-9._\-/]{1,80}$", plugins_branch):
        errors["PLUGINS_BRANCH"] = "PLUGINS_BRANCH has invalid characters."
    else:
        cleaned["PLUGINS_BRANCH"] = plugins_branch

    if errors:
        return False, errors, {}
    return True, {}, cleaned


def validate_db_url(db_url: str, db_name: str = "Zelretch") -> tuple[bool, str, "ConfigStorage | None"]:
    """Quick syntax check for the restore flow. Does NOT ping the DB."""
    from .storage import ConfigStorage  # local import to avoid cycle
    if not db_url:
        return False, "DATABASE_URL is required.", None
    if not _MONGO.match(db_url):
        return False, "DATABASE_URL must start with mongodb:// or mongodb+srv://", None
    if not re.match(r"^[A-Za-z0-9_\-]{1,64}$", db_name):
        return False, "DATABASE_NAME has invalid characters.", None
    try:
        storage = ConfigStorage(db_url, db_name)
    except ValueError as exc:
        return False, str(exc), None
    return True, "", storage


def validate_userbot(form: Any) -> tuple[bool, dict[str, str], dict[str, Any]]:
    """Validate the optional userbot-session step.

    Two valid modes:
      1. The user supplies an existing Pyrogram session string.
      2. The user lets the wizard create one (handled by ``session_helper``
         via interactive OTP flow). In that case the session string is
         already injected into the form by the JS layer.
    """
    errors: dict[str, str] = {}
    cleaned: dict[str, str] = {}

    session_string = (form.get("SESSION_STRING") or "").strip()
    if not session_string:
        errors["SESSION_STRING"] = (
            "Provide a session string, or use the interactive OTP flow below to generate one. "
            "Alternatively, click 'Skip' to deploy without a userbot session."
        )
        return False, errors, {}

    # Pyrogram session strings are base64-ish; usually 200+ chars.
    if len(session_string) < 80:
        errors["SESSION_STRING"] = "Session string looks too short to be valid."
        return False, errors, {}

    cleaned["SESSION_STRING"] = session_string
    return True, {}, cleaned


def validate_phone(phone: str) -> tuple[bool, str]:
    phone = (phone or "").strip()
    if not phone:
        return False, "Phone number is required."
    if not _PHONE.match(phone):
        return False, "Phone must be in international format, e.g. +8801XXXXXXXXX."
    return True, ""

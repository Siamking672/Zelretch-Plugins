"""
Configuration singleton.

Design goals (informed by both source projects):

1. **Validate at startup, fail loud.** Zelretch silently produces ``0`` / ``None``
   for missing vars and fails late at Pyrogram auth time. We hard-fail with a
   clear message instead.

2. **Layered config.** Static credentials come from env / .env. Tunable settings
   (templates, API keys, feature toggles) live in the DB via ``get_env`` /
   ``set_env`` commands, so users can change them at runtime without redeploying.
   This is the strongest idea from Zelretch's ``ENV`` class.

3. **Configurable command prefix.** Default ``.`` (period), expandable to a list
   via the ``HANDLERS`` env var (Zelretch convention). FoxUserbot's single-prefix
   ``config.ini`` approach is also supported at runtime via ``.setvar prefix``.

4. **Multi-tier permissions.** Owner → Sudo → Master → Devs → Banned/Muted,
   inspired by Zelretch's tiered model, but with IDs configurable via env
   instead of hardcoded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


REQUIRED_VARS = [
    "API_ID",
    "API_HASH",
]
# At least one of these must be present for the bot to actually run a client.
# The setup wizard lets the user skip session creation; in that case only
# BOT_TOKEN is required to start (assistant-bot mode). The user can later
# create a STRING_SESSION interactively via the `.session` command.
CLIENT_CREDENTIAL_VARS = ["STRING_SESSION", "BOT_TOKEN"]
OPTIONAL_VARS = {
    "STRING_SESSION": None,        # primary userbot account session
    "BOT_TOKEN": None,             # optional assistant bot
    "DATABASE_URL": None,          # if unset, use Telegram channel DB (or SQLite)
    "DATABASE_NAME": "astralbot",
    "DATABASE_CHAT_ID": None,      # Telegram channel ID for the Telegram channel DB backend
    "LOG_CHAT_ID": None,           # telegram log channel
    "OWNER_ID": None,              # auto-detected from session if missing
    "SUDO_USERS": "",              # space-separated user IDs
    "DEV_USERS": "",               # space-separated user IDs
    "HANDLERS": ". !",             # command prefixes
    "PLUGIN_REPO": "AstralBot/AstralModules",
    "PLUGIN_BRANCH": "main",
    "PLUGIN_PATH": "modules",      # sub-path inside the plugin repo
    "LOAD_BUILTIN": "true",        # load core builtins
    "DISABLED_PLUGINS": "",        # space-separated plugin names to skip
    "WORKERS": "8",
    "ENV_VAR_PREFIX": "ASTRALBOT",  # namespace for db.get_env/set_env keys
}


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass
class Config:
    """Validated configuration. Instantiated once at startup."""

    # Required
    api_id: int
    api_hash: str
    string_session: str

    # Optional but common
    bot_token: str | None = None
    database_url: str | None = None
    database_name: str = "astralbot"
    database_chat_id: int | None = None  # Telegram channel ID for TelegramChannelDatabase

    # Telegram-side logging
    log_chat_id: int | None = None

    # Permissions
    owner_id: int | None = None
    sudo_users: list[int] = field(default_factory=list)
    dev_users: list[int] = field(default_factory=list)

    # Command handling
    handlers: list[str] = field(default_factory=lambda: [".", "!"])
    primary_prefix: str = "."

    # Plugin system
    plugin_repo: str = "AstralBot/AstralModules"
    plugin_branch: str = "main"
    plugin_path: str = "modules"
    load_builtin: bool = True
    disabled_plugins: list[str] = field(default_factory=list)

    # Runtime
    workers: int = 8

    # Derived
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(default_factory=lambda: Path("userdata"))
    log_file: Path = field(default_factory=lambda: Path("astralbot.log"))

    @classmethod
    def from_env(cls) -> "Config":
        """Load and validate configuration from environment / .env file."""
        missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
        if missing:
            raise ConfigError(
                "Missing required environment variables: "
                + ", ".join(missing)
                + "\nRun `python -m astralbot` to launch the setup wizard."
            )

        try:
            api_id = int(os.environ["API_ID"])
        except ValueError as exc:
            raise ConfigError("API_ID must be an integer.") from exc

        # At least one client credential must be present
        string_session = os.getenv("STRING_SESSION") or None
        bot_token = os.getenv("BOT_TOKEN") or None
        if not string_session and not bot_token:
            raise ConfigError(
                "At least one of STRING_SESSION or BOT_TOKEN must be set.\n"
                "Run `python -m astralbot` to launch the setup wizard, "
                "or use `.session` from an existing bot to create a session."
            )

        handlers_raw = os.getenv("HANDLERS", ". !").strip()
        handlers = handlers_raw.split() if handlers_raw else ["."]
        if not handlers:
            handlers = ["."]

        log_chat_raw = os.getenv("LOG_CHAT_ID")
        try:
            log_chat_id = int(log_chat_raw) if log_chat_raw else None
        except ValueError as exc:
            raise ConfigError("LOG_CHAT_ID must be an integer.") from exc

        db_chat_raw = os.getenv("DATABASE_CHAT_ID")
        try:
            database_chat_id = int(db_chat_raw) if db_chat_raw else None
        except ValueError as exc:
            raise ConfigError("DATABASE_CHAT_ID must be an integer.") from exc

        owner_raw = os.getenv("OWNER_ID")
        try:
            owner_id = int(owner_raw) if owner_raw else None
        except ValueError as exc:
            raise ConfigError("OWNER_ID must be an integer.") from exc

        sudo = _parse_id_list(os.getenv("SUDO_USERS", ""))
        dev = _parse_id_list(os.getenv("DEV_USERS", ""))
        disabled = _parse_str_list(os.getenv("DISABLED_PLUGINS", ""))

        cfg = cls(
            api_id=api_id,
            api_hash=os.environ["API_HASH"],
            string_session=string_session or "",
            bot_token=bot_token,
            database_url=os.getenv("DATABASE_URL") or None,
            database_name=os.getenv("DATABASE_NAME", "astralbot"),
            database_chat_id=database_chat_id,
            log_chat_id=log_chat_id,
            owner_id=owner_id,
            sudo_users=sudo,
            dev_users=dev,
            handlers=handlers,
            primary_prefix=handlers[0],
            plugin_repo=os.getenv("PLUGIN_REPO", "AstralBot/AstralModules"),
            plugin_branch=os.getenv("PLUGIN_BRANCH", "main"),
            plugin_path=os.getenv("PLUGIN_PATH", "modules"),
            load_builtin=os.getenv("LOAD_BUILTIN", "true").lower() in ("1", "true", "yes"),
            disabled_plugins=disabled,
            workers=int(os.getenv("WORKERS", "8")),
        )

        # Ensure data directory exists
        cfg.data_dir.mkdir(parents=True, exist_ok=True)
        (cfg.data_dir / "plugins").mkdir(parents=True, exist_ok=True)
        (cfg.data_dir / "downloads").mkdir(parents=True, exist_ok=True)
        (cfg.data_dir / "temp").mkdir(parents=True, exist_ok=True)
        return cfg

    # --- Convenience helpers -----------------------------------------------

    def is_owner(self, user_id: int) -> bool:
        return self.owner_id is not None and user_id == self.owner_id

    def is_sudo(self, user_id: int) -> bool:
        return self.is_owner(user_id) or user_id in self.sudo_users

    def is_dev(self, user_id: int) -> bool:
        return user_id in self.dev_users

    def is_privileged(self, user_id: int) -> bool:
        """Owner, sudo, or dev — all bypass command restrictions."""
        return self.is_owner(user_id) or self.is_sudo(user_id) or self.is_dev(user_id)


def _parse_id_list(raw: str) -> list[int]:
    out: list[int] = []
    for chunk in (raw or "").split():
        try:
            out.append(int(chunk))
        except ValueError:
            continue
    return out


def _parse_str_list(raw: str) -> list[str]:
    return [c for c in (raw or "").split() if c]


def iter_env_keys() -> Iterable[str]:
    """Yield every AstralBot-related env var name (for docs / .env inspection)."""
    yield from REQUIRED_VARS
    yield from OPTIONAL_VARS.keys()

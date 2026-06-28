"""Secure MongoDB-backed configuration storage.

The deployment wizard persists every collected variable (API keys, bot
token, owner id, plugin repo, optional userbot session string, ...) into
a dedicated MongoDB collection so future deployments can restore from
just the database URL.

Security notes
--------------
* We never log full values. The :func:`mask` helper is used everywhere
  a value needs to be echoed back to the UI for review.
* Session strings are stored as-is (MongoDB TLS handles transport). For
  higher-security deployments, enable MongoDB client-side field level
  encryption; this layer intentionally stays simple so the wizard works
  on a plain MongoDB Atlas free tier.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Optional

from motor import motor_asyncio

CONFIG_COLLECTION = "deployment_config"
CONFIG_DOC_ID = "current"


_VALID_DB_NAME = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def mask(value: Optional[str], keep: int = 4) -> str:
    """Return a masked representation of a sensitive string.

    ``"abcdef123456"`` -> ``"abcd********"``. ``None`` -> ``"`` (empty).
    Used by the review screen and by logger-safe reprs.
    """
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "*" * (len(value) - keep)


class ConfigStorage:
    """Async wrapper around the ``deployment_config`` collection."""

    def __init__(self, database_url: str, database_name: str = "Zelretch"):
        if not database_url:
            raise ValueError("DATABASE_URL is required")
        if not _VALID_DB_NAME.match(database_name):
            raise ValueError(f"Invalid DATABASE_NAME: {database_name!r}")
        self.database_url = database_url
        self.database_name = database_name
        self._client: Optional[motor_asyncio.AsyncIOMotorClient] = None
        self._db = None

    async def __aenter__(self) -> "ConfigStorage":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def connect(self) -> None:
        self._client = motor_asyncio.AsyncIOMotorClient(self.database_url)
        # Force connection so we surface auth/network errors immediately.
        await self._client.admin.command("ping")
        self._db = self._client[self.database_name]

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None

    @property
    def collection(self):
        if self._db is None:
            raise RuntimeError("ConfigStorage not connected; call connect() first")
        return self._db[CONFIG_COLLECTION]

    def get_collection(self, name: str):
        """Return any collection from the connected database.

        Used by the orchestrator to write the userbot session string
        into the bot's own ``session`` collection (which the runtime
        reads at startup).
        """
        if self._db is None:
            raise RuntimeError("ConfigStorage not connected; call connect() first")
        if not re.match(r"^[A-Za-z0-9_\-]{1,120}$", name):
            raise ValueError(f"Invalid collection name: {name!r}")
        return self._db[name]

    async def save_config(self, config: dict[str, Any]) -> None:
        """Upsert the deployment configuration document."""
        now = datetime.datetime.utcnow().isoformat(timespec="seconds")
        await self.collection.update_one(
            {"_id": CONFIG_DOC_ID},
            {
                "$set": {
                    "config": config,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    async def fetch_config(self) -> Optional[dict[str, Any]]:
        """Return the saved configuration, or ``None`` if absent."""
        doc = await self.collection.find_one({"_id": CONFIG_DOC_ID})
        if not doc:
            return None
        return doc.get("config")


async def test_connection(database_url: str, database_name: str = "Zelretch") -> tuple[bool, str]:
    """Attempt to ping the database. Returns ``(ok, message)``."""
    try:
        storage = ConfigStorage(database_url, database_name)
        await storage.connect()
        await storage.close()
        return True, "Connected successfully."
    except Exception as exc:  # noqa: BLE001 - we want to surface every error
        return False, str(exc)


async def fetch_saved_config(database_url: str, database_name: str = "Zelretch") -> tuple[bool, Optional[dict[str, Any]], str]:
    """Connect, fetch saved config, return ``(ok, config_or_none, message)``."""
    try:
        async with ConfigStorage(database_url, database_name) as storage:
            cfg = await storage.fetch_config()
            if not cfg:
                return True, None, "Connected, but no saved configuration was found in this database."
            return True, cfg, "Configuration restored."
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)

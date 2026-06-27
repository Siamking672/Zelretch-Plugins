"""astralbot.core package — re-exports for convenience."""

from astralbot.core.config import Config, ConfigError
from astralbot.core.database import (
    Database,
    open_database,
    SQLiteDatabase,
    MongoDBDatabase,
    TelegramChannelDatabase,
)
from astralbot.core.client import (
    AstralClient,
    build_clients,
    stop_clients,
    ensure_log_channel,
    ensure_database_channel,
)
from astralbot.core.loader import PluginLoader, PluginManifest
from astralbot.core.logger import setup_logging, setup_logging_async, TelegramLogHandler
from astralbot.core.permissions import can_run, PermissionDenied
from astralbot.core.updater import clone_or_pull_plugin_repo, restart_process

__all__ = [
    "Config",
    "ConfigError",
    "Database",
    "open_database",
    "SQLiteDatabase",
    "MongoDBDatabase",
    "TelegramChannelDatabase",
    "AstralClient",
    "build_clients",
    "stop_clients",
    "ensure_log_channel",
    "ensure_database_channel",
    "PluginLoader",
    "PluginManifest",
    "setup_logging",
    "setup_logging_async",
    "TelegramLogHandler",
    "can_run",
    "PermissionDenied",
    "clone_or_pull_plugin_repo",
    "restart_process",
]

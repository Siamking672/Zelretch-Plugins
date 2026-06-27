"""
AstralBot — a refined Telegram userbot framework.

Combines the strongest ideas from Zelretch (retheme of Hellbot) and FoxUserbot
into a single, polished, developer-friendly codebase.

Public API surface (re-exported here so plugins can simply do
``from astralbot import on_command, help_menu, client, Config, db``):

- ``Config``        — validated configuration singleton
- ``client``        — primary Pyrogram client (after startup)
- ``clients``       — list of all active clients (multi-account)
- ``db``            — database backend (SQLite default, Mongo optional)
- ``on_command``    — decorator registering a command on every client
- ``on_event``      — decorator registering a raw Pyrogram filter handler
- ``help_menu``     — fluent help registry
- ``LOGS``          — root logger
- ``__version__``   — semantic version string
"""

from __future__ import annotations

__version__ = "1.0.0"
__codename__ = "Astral"
__license__ = "GPL-3.0"

# Lazy imports — these are bound at startup in core.initializer.
# Importing astralbot before main() runs is safe; the symbols below
# are populated by the time any plugin's @on_command handler fires.
Config = None  # type: ignore[assignment]
client = None  # type: ignore[assignment]
clients = []  # type: ignore[list]
db = None  # type: ignore[assignment]
LOGS = None  # type: ignore[assignment]


def _bind_startup_objects(config, primary_client, all_clients, database, logs):
    """Called by core.initializer at the end of startup."""
    global Config, client, clients, db, LOGS
    Config = config
    client = primary_client
    clients = all_clients
    db = database
    LOGS = logs


# Re-exported lazily so `from astralbot import on_command` works in plugins.
def on_command(*args, **kwargs):  # pragma: no cover — bound at runtime
    from astralbot.plugins.decorator import on_command as _impl
    return _impl(*args, **kwargs)


def on_event(*args, **kwargs):  # pragma: no cover — bound at runtime
    from astralbot.plugins.decorator import on_event as _impl
    return _impl(*args, **kwargs)


class _HelpMenuProxy:
    """Thin proxy so `from astralbot import help_menu` resolves after startup."""
    def add(self, *a, **kw):
        from astralbot.plugins.help import registry
        return registry.add(*a, **kw)

    def register_module(self, *a, **kw):
        from astralbot.plugins.help import registry
        return registry.register_module(*a, **kw)

    def all_modules(self):
        from astralbot.plugins.help import registry
        return registry.all_modules()

    def render_help(self, *a, **kw):
        from astralbot.plugins.help import registry
        return registry.render_help(*a, **kw)


help_menu = _HelpMenuProxy()

"""Restart builtin — graceful process restart."""

from __future__ import annotations

import asyncio
import os
import sys

from astralbot import on_command, help_menu, Config, LOGS
from astralbot.core.updater import restart_process

__plugin_name__ = "Restart"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Restart or shut down the bot."
__plugin_category__ = "core"


@on_command("restart", description="Restart the bot.", permission="owner")
async def restart_cmd(client, message):
    await message.edit_text("🔄 Restarting AstralBot...")
    LOGS.info("Restart requested by %s", message.from_user.id if message.from_user else "?")

    # Try graceful shutdown first
    from astralbot import clients, db
    if clients:
        from astralbot.core.client import stop_clients
        await stop_clients(clients)
    if db:
        await db.close()

    # execv replaces the current process
    restart_process()


@on_command("shutdown", description="Shut down the bot.", permission="owner")
async def shutdown_cmd(client, message):
    await message.edit_text("👋 Shutting down...")
    LOGS.info("Shutdown requested by %s", message.from_user.id if message.from_user else "?")
    from astralbot import clients, db
    if clients:
        from astralbot.core.client import stop_clients
        await stop_clients(clients)
    if db:
        await db.close()
    # Force exit
    os._exit(0)


help_menu.add(
    command="restart",
    description="Restart the bot process.",
    example=".restart",
    category="core",
    plugin="restart",
).register()

help_menu.add(
    command="shutdown",
    description="Shut down the bot.",
    example=".shutdown",
    category="core",
    plugin="restart",
).register()

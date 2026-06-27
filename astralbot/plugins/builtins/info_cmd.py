"""Info builtin — show system / deployment info."""

from __future__ import annotations

import os
import platform
import sys
import time

from astralbot import on_command, help_menu, __version__, Config, LOGS
from astralbot.plugins.builtins.alive import _fmt_uptime

__plugin_name__ = "Info"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Show system and deployment info."
__plugin_category__ = "core"

_START = time.time()


@on_command("info", description="Show system info.", permission="sudo")
async def info_cmd(client, message):
    me = await client.get_me()
    uptime = _fmt_uptime(time.time() - _START)

    # Detect deployment environment
    env = "local"
    if os.environ.get("DYNO"):
        env = "heroku"
    elif os.environ.get("DOCKER"):
        env = "docker"
    elif os.environ.get("RAILWAY_PROJECT_ID"):
        env = "railway"
    elif os.environ.get("RENDER_SERVICE_ID"):
        env = "render"
    elif os.path.exists("/.dockerenv"):
        env = "docker"

    # Database backend
    db_backend = "MongoDB" if Config.database_url else "SQLite"

    await message.edit_text(
        f"✨ **AstralBot v{__version__}**\n"
        f"\n"
        f"**Account:** @{me.username} (`{me.id}`)\n"
        f"**Owner:** `{Config.owner_id}`\n"
        f"**Prefixes:** `{'`, `'.join(Config.handlers)}`\n"
        f"\n"
        f"**System**\n"
        f"  Python: `{sys.version.split()[0]}`\n"
        f"  Platform: `{platform.platform()}`\n"
        f"  Uptime: `{uptime}`\n"
        f"  PID: `{os.getpid()}`\n"
        f"\n"
        f"**Deployment**\n"
        f"  Environment: `{env}`\n"
        f"  Database: `{db_backend}`\n"
        f"  Plugin repo: `{Config.plugin_repo}@{Config.plugin_branch}`\n"
        f"  Multi-account: `{len(__import__('astralbot').clients)}` client(s)"
    )


help_menu.add(
    command="info",
    description="Show system and deployment info.",
    example=".info",
    category="core",
    plugin="info",
).register()

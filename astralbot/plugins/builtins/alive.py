"""Alive builtin — shows bot uptime, account, plugin count."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from astralbot import on_command, help_menu, __version__
from astralbot.core.loader import PluginLoader  # type: ignore

__plugin_name__ = "Alive"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Show bot status: version, uptime, plugins loaded."
__plugin_category__ = "core"

_START_TIME = time.time()


def _fmt_uptime(seconds: float) -> str:
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


@on_command("alive", description="Show bot status.", permission="sudo")
async def alive_cmd(client, message):
    me = await client.get_me()
    uptime = _fmt_uptime(time.time() - _START_TIME)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Count loaded plugins — find the loader via the loaded registry
    from astralbot.plugins.decorator import _handler_registry
    plugin_count = len(_handler_registry)

    await message.edit_text(
        f"✨ **AstralBot is Alive!**\n"
        f"\n"
        f"  **Version:** `{__version__}`\n"
        f"  **Account:** @{me.username} (`{me.id}`)\n"
        f"  **Uptime:** `{uptime}`\n"
        f"  **Plugins loaded:** `{plugin_count}`\n"
        f"  **Time:** `{now}`\n"
        f"  **PID:** `{os.getpid()}`"
    )


help_menu.add(
    command="alive",
    description="Show bot status: version, uptime, plugins loaded.",
    example=".alive",
    category="core",
    plugin="alive",
).register()

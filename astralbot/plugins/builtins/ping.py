"""Ping builtin — measures bot-to-Telegram latency."""

from __future__ import annotations

import time

from astralbot import on_command, help_menu, __version__

__plugin_name__ = "Ping"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Check bot-to-Telegram round-trip latency."
__plugin_category__ = "core"


@on_command("ping", description="Check bot latency.", permission="sudo")
async def ping_cmd(client, message):
    start = time.perf_counter()
    msg = await message.edit_text("🏓 Pinging...")
    elapsed_ms = (time.perf_counter() - start) * 1000
    await msg.edit_text(
        f"🏓 **Pong!**\n"
        f"  Latency: `{elapsed_ms:.2f} ms`\n"
        f"  AstralBot v`{__version__}`"
    )


help_menu.add(
    command="ping",
    description="Check bot-to-Telegram round-trip latency.",
    example=".ping",
    category="core",
    plugin="ping",
).register()

"""Update builtin — pull latest external plugins and restart."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config, LOGS
from astralbot.core.updater import clone_or_pull_plugin_repo, restart_process

__plugin_name__ = "Update"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Pull latest external plugins and restart."
__plugin_category__ = "core"


@on_command("update", description="Pull latest external plugins and restart.", permission="owner")
async def update_cmd(client, message):
    msg = await message.edit_text("⏳ Pulling latest plugins...")
    try:
        path = await clone_or_pull_plugin_repo(Config)
        if path:
            await msg.edit_text(f"✅ Plugins updated. Restarting...")
        else:
            await msg.edit_text("⚠️ No updates available or fetch failed. Restarting anyway...")
    except Exception as exc:
        LOGS.exception("Update failed: %s", exc)
        await msg.edit_text(f"❌ Update failed: `{exc}`\nRestarting anyway...")

    # Restart to pick up changes
    from astralbot import clients, db
    if clients:
        from astralbot.core.client import stop_clients
        await stop_clients(clients)
    if db:
        await db.close()
    restart_process()


help_menu.add(
    command="update",
    description="Pull latest external plugins and restart.",
    example=".update",
    category="core",
    plugin="update",
).register()

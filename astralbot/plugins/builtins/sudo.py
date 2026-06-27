"""Sudo / master user management builtins."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config, db

__plugin_name__ = "Sudo"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Manage master / sudo users and check your permission tier."
__plugin_category__ = "core"


@on_command("addmaster", description="Add a master user (sudo tier).", permission="owner")
async def addmaster_cmd(client, message):
    target = await _resolve_target_user(client, message)
    if not target:
        return await message.edit_text(
            f"Reply to a user or specify an ID: `{Config.primary_prefix}addmaster <id|reply>`"
        )
    await db.add_master(target)
    await message.edit_text(f"✅ Added `{target}` to master users.")


@on_command("delmaster", description="Remove a master user.", permission="owner")
async def delmaster_cmd(client, message):
    target = await _resolve_target_user(client, message)
    if not target:
        return await message.edit_text(
            f"Reply to a user or specify an ID: `{Config.primary_prefix}delmaster <id|reply>`"
        )
    await db.del_master(target)
    await message.edit_text(f"🗑️ Removed `{target}` from master users.")


@on_command(["masters", "listmasters"], description="List master users.", permission="owner")
async def masters_cmd(client, message):
    masters = await db.list_masters()
    if not masters:
        return await message.edit_text("No master users set.")
    lines = ["**Master users:**\n"]
    for uid in masters:
        lines.append(f"  • `{uid}`")
    await message.edit_text("\n".join(lines))


@on_command("whoami", description="Show your permission tier.", permission="public")
async def whoami_cmd(client, message):
    if not message.from_user:
        return await message.edit_text("Cannot identify you.")
    uid = message.from_user.id
    is_master = await db.is_master(uid)
    tier = "public"
    if Config.is_owner(uid):
        tier = "owner"
    elif Config.is_dev(uid):
        tier = "dev"
    elif Config.is_sudo(uid):
        tier = "sudo"
    elif is_master:
        tier = "master"
    await message.edit_text(
        f"🆔 You are `{message.from_user.first_name}` (`{uid}`)\n"
        f"📊 Tier: `{tier}`"
    )


async def _resolve_target_user(client, message) -> int | None:
    """Get a user ID from reply or command arg."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    if len(message.command) >= 2:
        try:
            return int(message.command[1])
        except ValueError:
            pass
    return None


# Help entries
for cmd, desc, ex in [
    ("addmaster", "Add a master user (sudo tier).", ".addmaster (reply to user)"),
    ("delmaster", "Remove a master user.", ".delmaster (reply to user)"),
    ("masters", "List all master users.", ".masters"),
    ("whoami", "Show your permission tier.", ".whoami"),
]:
    help_menu.add(
        command=cmd,
        description=desc,
        example=ex,
        category="core",
        plugin="sudo",
    ).register()

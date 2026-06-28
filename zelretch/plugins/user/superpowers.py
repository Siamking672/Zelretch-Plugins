import asyncio
import datetime

from kurigram import Client, filters
from kurigram.enums import ChatType, ChatMemberStatus as CMS
from kurigram.errors import FloodWait
from kurigram.types import ChatMemberUpdated, ChatPermissions, ChatPrivileges, Message

from zelretch.functions.templates import gban_templates

from . import Config, HelpMenu, Symbols, custom_handler, db, zelretch, on_message


@on_message("gpromote", allow_master=True)
async def globalpromote(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await zelretch.delete(
                message, "Reply to a user or pass a username/id to gpromote."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{str(e)}`")
        reason = (
            message.text.split(None, 2)[2]
            if len(message.text.split()) > 2
            else "No reason provided."
        )
    else:
        user = message.reply_to_message.from_user
        reason = await zelretch.input(message) or "No reason provided."

    if user.is_self:
        return await zelretch.delete(message, "I can't gpromote myself.")

    privileges = ChatPrivileges(
        can_manage_chat=True,
        can_delete_messages=True,
        can_manage_video_chats=True,
        can_restrict_members=False,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=True,
        is_anonymous=False,
    )

    success = 0
    failed = 0
    kaleido = await zelretch.edit(message, f"Gpromote initiated on {user.mention}...")

    async for dialog in client.get_dialogs():
        if dialog.chat.type in [
            ChatType.CHANNEL,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ]:
            try:
                await dialog.chat.promote_member(user.id, privileges)
                success += 1
            except FloodWait as e:
                await kaleido.edit(
                    f"Gpromote initiated on {user.mention}...\nSleeping for {e.value} seconds due to floodwait..."
                )
                await asyncio.sleep(e.value)
                await dialog.chat.promote_member(user.id, privileges)
                success += 1
                await kaleido.edit(f"Gpromote initiated on {user.mention}...")
            except BaseException:
                failed += 1

    await kaleido.edit(
        await gban_templates(
            gtype="𝖦-𝖯𝗋𝗈𝗆𝗈𝗍𝖾",
            name=user.mention,
            success=success,
            failed=failed,
            reason=reason,
        )
    )

    await zelretch.check_and_log(
        "gpromote",
        f"**User:** {user.mention} (`{user.id}`)\n**By: {client.me.mention}**\n\n**Reason:** `{reason}`",
    )


@on_message("gdemote", allow_master=True)
async def globaldemote(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await zelretch.delete(
                message, "Reply to a user or pass a username/id to gdemote."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{str(e)}`")
        reason = (
            message.text.split(None, 2)[2]
            if len(message.text.split()) > 2
            else "No reason provided."
        )
    else:
        user = message.reply_to_message.from_user
        reason = await zelretch.input(message) or "No reason provided."

    if user.is_self:
        return await zelretch.delete(message, "I can't gdemote myself.")

    privileges = ChatPrivileges(
        can_manage_chat=False,
        can_delete_messages=False,
        can_manage_video_chats=False,
        can_restrict_members=False,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False,
        is_anonymous=False,
    )

    success = 0
    failed = 0
    kaleido = await zelretch.edit(message, f"Gdemote initiated on {user.mention}...")

    async for dialog in client.get_dialogs():
        if dialog.chat.type in [
            ChatType.CHANNEL,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ]:
            try:
                await dialog.chat.promote_member(user.id, privileges)
                success += 1
            except FloodWait as e:
                await kaleido.edit(
                    f"Gdemote initiated on {user.mention}...\nSleeping for {e.value} seconds due to floodwait..."
                )
                await asyncio.sleep(e.value)
                await dialog.chat.promote_member(user.id, privileges)
                success += 1
                await kaleido.edit(f"Gdemote initiated on {user.mention}...")
            except BaseException:
                failed += 1

    await kaleido.edit(
        await gban_templates(
            gtype="𝖦-𝖣𝖾𝗆𝗈𝗍𝖾",
            name=user.mention,
            success=success,
            failed=failed,
            reason=reason,
        )
    )

    await zelretch.check_and_log(
        "gdemote",
        f"**User:** {user.mention} (`{user.id}`)\n**By: {client.me.mention}**\n\n**Reason:** `{reason}`",
    )


@on_message("gban", allow_master=True)
async def globalban(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await zelretch.delete(
                message, "Reply to a user or pass a username/id to gban."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{str(e)}`")
        reason = (
            message.text.split(None, 2)[2]
            if len(message.text.split()) > 2
            else "No reason provided."
        )
    else:
        user = message.reply_to_message.from_user
        reason = await zelretch.input(message) or "No reason provided."

    if user.is_self:
        return await zelretch.delete(message, "I can't gban myself.")

    if user.id in Config.AUTH_USERS:
        return await zelretch.delete(message, "I can't gban my auth user.")

    if user.id in Config.BANNED_USERS:
        return await zelretch.delete(message, "This user is already gbanned.")

    if user.id in Config.DEVS:
        return await zelretch.delete(message, "I can't gban my devs.")

    success = 0
    failed = 0
    kaleido = await zelretch.edit(message, f"Gban initiated on {user.mention}...")

    await db.add_gban(user.id, reason)
    Config.BANNED_USERS.add(user.id)

    async for dialog in client.get_dialogs():
        if dialog.chat.type in [
            ChatType.CHANNEL,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ]:
            try:
                await dialog.chat.ban_member(user.id)
                success += 1
            except FloodWait as e:
                await kaleido.edit(
                    f"Gban initiated on {user.mention}...\nSleeping for {e.value} seconds due to floodwait..."
                )
                await asyncio.sleep(e.value)
                await dialog.chat.ban_member(user.id)
                success += 1
                await kaleido.edit(f"Gban initiated on {user.mention}...")
            except BaseException:
                failed += 1

    await kaleido.edit(
        await gban_templates(
            gtype="𝖦-𝖡𝖺𝗇",
            name=user.mention,
            success=success,
            failed=failed,
            reason=reason,
        )
    )

    await zelretch.check_and_log(
        "gban",
        f"**User:** {user.mention} (`{user.id}`)\n**By: {client.me.mention}**\n\n**Reason:** `{reason}`",
    )


@on_message("ungban", allow_master=True)
async def unglobalban(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await zelretch.delete(
                message, "Reply to a user or pass a username/id to ungban."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{str(e)}`")
    else:
        user = message.reply_to_message.from_user

    if user.id not in Config.BANNED_USERS:
        await zelretch.delete(
            message,
            "This user is not gbanned. Unbanning in all my admin chats anyway...",
        )
    else:
        reason = await db.rm_gban(user.id)
        Config.BANNED_USERS.remove(user.id)
        await zelretch.edit(
            message,
            f"**𝖴𝗇𝗀𝖻𝖺𝗇𝗇𝖾𝖽** {user.mention}!\n\n**𝖦𝖻𝖺𝗇 𝖱𝖾𝖺𝗌𝗈𝗇 𝗐𝖺𝗌:** `{reason}`",
        )

    async for dialog in client.get_dialogs():
        if dialog.chat.type in [
            ChatType.CHANNEL,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ]:
            try:
                await dialog.chat.unban_member(user.id)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await dialog.chat.unban_member(user.id)
            except BaseException:
                pass

    await zelretch.check_and_log(
        "ungban",
        f"**User:** {user.mention} (`{user.id}`)\n**By: {message.from_user.mention}**",
    )


@on_message("gkick", allow_master=True)
async def globalkick(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await zelretch.delete(
                message, "Reply to a user or pass a username/id to gkick."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{str(e)}`")
        reason = (
            message.text.split(None, 2)[2]
            if len(message.text.split()) > 2
            else "No reason provided."
        )
    else:
        user = message.reply_to_message.from_user
        reason = await zelretch.input(message) or "No reason provided."

    if user.is_self:
        return await zelretch.delete(message, "I can't gkick myself.")

    if user.id in Config.AUTH_USERS:
        return await zelretch.delete(message, "I can't gkick my auth user.")

    if user.id in Config.BANNED_USERS:
        return await zelretch.delete(
            message, "This user is already gbanned. There's no point in kicking them!"
        )

    if user.id in Config.DEVS:
        return await zelretch.delete(message, "I can't gkick my devs.")

    success = 0
    failed = 0
    kaleido = await zelretch.edit(message, f"Gkick initiated on {user.mention}...")

    async for dialog in client.get_dialogs():
        if dialog.chat.type in [
            ChatType.CHANNEL,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ]:
            try:
                await dialog.chat.ban_member(
                    user.id, datetime.datetime.now() + datetime.timedelta(seconds=35)
                )
                success += 1
            except FloodWait as e:
                await kaleido.edit(
                    f"Gkick initiated on {user.mention}...\nSleeping for {e.value} seconds due to floodwait..."
                )
                await asyncio.sleep(e.value)
                await dialog.chat.ban_member(
                    user.id, datetime.datetime.now() + datetime.timedelta(seconds=35)
                )
                success += 1
                await kaleido.edit(f"Gkick initiated on {user.mention}...")
            except BaseException:
                failed += 1

    await kaleido.edit(
        await gban_templates(
            gtype="𝖦-𝖪𝗂𝖼𝗄",
            name=user.mention,
            success=success,
            failed=failed,
            reason=reason,
        )
    )

    await zelretch.check_and_log(
        "gkick",
        f"**User:** {user.mention} (`{user.id}`)\n**By: {client.me.mention}**\n\n**Reason:** `{reason}`",
    )


@on_message("gmute", allow_master=True)
async def globalmute(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await zelretch.delete(
                message, "Reply to a user or pass a username/id to gmute."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{str(e)}`")
        reason = (
            message.text.split(None, 2)[2]
            if len(message.text.split()) > 2
            else "No reason provided."
        )
    else:
        user = message.reply_to_message.from_user
        reason = await zelretch.input(message) or "No reason provided."

    if user.is_self:
        return await zelretch.delete(message, "I can't gmute myself.")

    if user.id in Config.AUTH_USERS:
        return await zelretch.delete(message, "I can't gmute my auth user.")

    if user.id in Config.MUTED_USERS:
        return await zelretch.delete(message, "This user is already gmuted.")

    if user.id in Config.DEVS:
        return await zelretch.delete(message, "I can't gmute my devs.")

    permissions = ChatPermissions(can_send_messages=False)
    success = 0
    failed = 0
    kaleido = await zelretch.edit(message, f"Gmute initiated on {user.mention}...")

    await db.add_gmute(user.id, reason)
    Config.MUTED_USERS.add(user.id)

    async for dialog in client.get_dialogs():
        if dialog.chat.type in [
            ChatType.CHANNEL,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ]:
            try:
                await dialog.chat.restrict_member(user.id, permissions)
                success += 1
            except FloodWait as e:
                await kaleido.edit(
                    f"Gmute initiated on {user.mention}...\nSleeping for {e.value} seconds due to floodwait..."
                )
                await asyncio.sleep(e.value)
                await dialog.chat.restrict_member(user.id, permissions)
                success += 1
                await kaleido.edit(f"Gmute initiated on {user.mention}...")
            except BaseException:
                failed += 1

    await kaleido.edit(
        await gban_templates(
            gtype="𝖦-𝖬𝗎𝗍𝖾",
            name=user.mention,
            success=success,
            failed=failed,
            reason=reason,
        )
    )

    await zelretch.check_and_log(
        "gmute",
        f"**User:** {user.mention} (`{user.id}`)\n**By: {client.me.mention}**\n\n**Reason:** `{reason}`",
    )


@on_message("ungmute", allow_master=True)
async def unglobalmute(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await zelretch.delete(
                message, "Reply to a user or pass a username/id to ungmute."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{str(e)}`")
    else:
        user = message.reply_to_message.from_user

    if user.id not in Config.MUTED_USERS:
        await zelretch.delete(
            message, "This user is not gmuted. Unmuting in all my admin chats anyway..."
        )
    else:
        reason = await db.rm_gmute(user.id)
        Config.MUTED_USERS.remove(user.id)
        await zelretch.edit(
            message,
            f"**𝖴𝗇𝗀𝗆𝗎𝗍𝖾𝖽** {user.mention}!\n\n**𝖦𝗆𝗎𝗍𝖾 𝖱𝖾𝖺𝗌𝗈𝗇 𝗐𝖺𝗌:** `{reason}`",
        )

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_send_polls=True,
        can_add_web_page_previews=True,
        can_change_info=True,
        can_invite_users=True,
        can_pin_messages=True,
    )

    async for dialog in client.get_dialogs():
        if dialog.chat.type in [
            ChatType.CHANNEL,
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ]:
            try:
                await dialog.chat.restrict_member(user.id, permissions)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await dialog.chat.restrict_member(user.id, permissions)
            except BaseException:
                pass

    await zelretch.check_and_log(
        "ungmute",
        f"**User:** {user.mention} (`{user.id}`)\n**By: {message.from_user.mention}**",
    )


@on_message("gbanlist", allow_master=True)
async def gbanlist(_, message: Message):
    gban_users = await db.get_gban()
    if not gban_users:
        return await zelretch.delete(message, "No gbanned users.")

    kaleido = await zelretch.edit(message, "Fetching gbanned users...")
    text = f"**💥 𝖦𝖻𝖺𝗇𝗇𝖾𝖽 𝖴𝗌𝖾𝗋𝗌:** __{len(gban_users)}__\n\n"

    for user in gban_users:
        text += f"{Symbols.bullet} `{user['user_id']}` | __{user['reason']}__\n\n"

    await kaleido.edit(text)


@on_message("gmutelist", allow_master=True)
async def gmutelist(_, message: Message):
    gmute_users = await db.get_gmute()
    if not gmute_users:
        return await zelretch.delete(message, "No gmuted users.")

    kaleido = await zelretch.edit(message, "Fetching gmuted users...")
    text = f"**😶 𝖦𝗆𝗎𝗍𝖾𝖽 𝖴𝗌𝖾𝗋𝗌:** __{len(gmute_users)}__\n\n"

    for user in gmute_users:
        text += f"{Symbols.bullet} `{user['user_id']}` | __{user['reason']}__\n\n"

    await kaleido.edit(text)


@Client.on_chat_member_updated()
async def globalbanwatcher(_, u: ChatMemberUpdated):
    if not (u.new_chat_member and u.new_chat_member.status not in {CMS.BANNED, CMS.LEFT, CMS.RESTRICTED} and not u.old_chat_member):
        return
    
    user = u.new_chat_member.user if u.new_chat_member else u.from_user

    if await db.is_gbanned(user.id):
        gban_data = await db.get_gban_user(user.id)
        watchertext = f"**𝖦𝖻𝖺𝗇𝗇𝖾𝖽 𝖴𝗌𝖾𝗋 𝗃𝗈𝗂𝗇𝖾𝖽 𝗍𝗁𝖾 𝖼𝗁𝖺𝗍! \n\n{Symbols.bullet} 𝖦𝖻𝖺𝗇 𝖱𝖾𝖺𝗌𝗈𝗇 𝗐𝖺𝗌:** __{gban_data['reason']}__\n**{Symbols.bullet} 𝖦𝖻𝖺𝗇 𝖣𝖺𝗍𝖾:** __{gban_data['date']}__\n\n"

        try:
            await _.ban_chat_member(u.chat.id, user.id)
            watchertext += f"**𝖲𝗈𝗋𝗋𝗒 𝖨 𝖼𝖺𝗇'𝗍 𝗌𝖾𝖾 𝗒𝗈𝗎 𝗂𝗇 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍!**"
        except BaseException:
            watchertext += f"Reported to @admins"

        await _.send_message(u.chat.id, watchertext)
    return

HelpMenu("superpowers").add(
    "gpromote",
    "<reply to user> or <username/id> <reason (optional)>",
    "Promote a user to admin in every chat where the userbot has promote-member permission.",
    "gpromote @ZelretchUser trusted moderator",
).add(
    "gdemote",
    "<reply to user> or <username/id> <reason (optional)>",
    "Remove admin privileges from a user in every chat where the userbot has promote-member permission.",
    "gdemote @ZelretchUser no longer needed",
).add(
    "gban",
    "<reply to user> or <username/id> <reason (optional)>",
    "Ban a user from every chat where the userbot has ban permission. The ban is recorded so new chats the userbot joins will also apply it.",
    "gban @ZelretchUser repeated spam",
).add(
    "ungban",
    "<reply to user> or <username/id>",
    "Lift a global ban. The user is unbanned from every chat where the userbot has ban permission and removed from the gban list.",
    "ungban @ZelretchUser",
).add(
    "gkick",
    "<reply to user> or <username/id> <reason (optional)>",
    "Kick a user from every chat where the userbot has ban permission. The user can rejoin if they have an invite link.",
    "gkick @ZelretchUser warning issued",
).add(
    "gmute",
    "<reply to user> or <username/id> <reason (optional)>",
    "Mute a user in every chat where the userbot has restrict permission. The mute is recorded so new chats the userbot joins will also apply it.",
    "gmute @ZelretchUser excessive mentions",
).add(
    "ungmute",
    "<reply to user> or <username/id>",
    "Lift a global mute. The user is unmuted in every chat where the userbot has restrict permission and removed from the gmute list.",
    "ungmute @ZelretchUser",
).add(
    "gbanlist",
    None,
    "List every user currently on the global ban list, along with the recorded reason and date.",
    "gbanlist",
).add(
    "gmutelist",
    None,
    "List every user currently on the global mute list, along with the recorded reason and date.",
    "gmutelist",
).info(
    "Global administrative actions — apply a single ban, mute, kick, promote, or demote across every chat the userbot administers."
).done()

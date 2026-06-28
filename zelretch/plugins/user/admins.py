import asyncio

from kurigram import Client, filters
from kurigram.types import ChatPermissions, ChatPrivileges, Message

from zelretch.core import LOGS

from . import HelpMenu, custom_handler, db, group_only, handler, zelretch, on_message


@on_message(
    "promote",
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def promote(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await zelretch.delete(
            message, "𝖭𝖾𝖾𝖽 𝖺 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾/𝗂𝖽 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗎𝗌𝖾𝗋 𝗍𝗈 𝗉𝗋𝗈𝗆𝗈𝗍𝖾 𝗍𝗁𝖾𝗆!"
        )

    title = ""
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        title = await zelretch.input(message)
    else:
        user = await client.get_users(message.command[1])
        if len(message.command) > 2:
            title = (await zelretch.input(message)).split(" ", 1)[1].strip()

    try:
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
        await message.chat.promote_member(user.id, privileges)
        await client.set_administrator_title(message.chat.id, user.id, title)
    except Exception as e:
        return await zelretch.error(message, e)

    await zelretch.delete(message, f"**💫 𝖯𝗋𝗈𝗆𝗈𝗍𝖾𝖽 {user.mention} 𝗌𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒!**")
    await zelretch.check_and_log(
        "promote",
        f"**Promoted User**\n\n**User:** {user.mention}\n**User ID:** `{user.id}`\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message(
    "demote",
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def demote(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await zelretch.delete(
            message, "𝖭𝖾𝖾𝖽 𝖺 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾/𝗂𝖽 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗎𝗌𝖾𝗋 𝗍𝗈 𝖽𝖾𝗆𝗈𝗍𝖾 𝗍𝗁𝖾𝗆!"
        )

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = await client.get_users(message.command[1])
    try:
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
        await message.chat.promote_member(user.id, privileges)
    except Exception as e:
        return await zelretch.error(message, e)

    await zelretch.delete(message, f"**🙄 𝖣𝖾𝗆𝗈𝗍𝖾𝖽 {user.mention} 𝗌𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒!**")
    await zelretch.check_and_log(
        "demote",
        f"**Demoted User**\n\n**User:** {user.mention}\n**User ID:** `{user.id}`\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message(
    ["ban", "dban"],
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def ban(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if len(message.command) < 2:
            reason = None
        else:
            reason = await zelretch.input(message)
        if message.command[0][0].lower() == "d":
            try:
                await message.reply_to_message.delete()
            except Exception:
                pass
    elif len(message.command) == 2:
        user = await client.get_users(message.command[1])
        reason = None
    elif len(message.command) > 2:
        user = await client.get_users(message.command[1])
        reason = (await zelretch.input(message)).split(" ", 1)[1].strip()
    else:
        return await zelretch.delete(
            message, "𝖭𝖾𝖾𝖽 𝖺 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾/𝗂𝖽 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗎𝗌𝖾𝗋 𝗍𝗈 𝖻𝖺𝗇 𝗍𝗁𝖾𝗆!"
        )

    try:
        await message.chat.ban_member(user.id)
    except Exception as e:
        return await zelretch.error(message, e)

    reason = reason if reason else "Not Specified"
    await zelretch.delete(
        message,
        f"**☠️ 𝖡𝖺𝗇𝗇𝖾𝖽 {user.mention} 𝗌𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒!**\n**𝖱𝖾𝖺𝗌𝗈𝗇:** `{reason}`",
        30,
    )
    await zelretch.check_and_log(
        "ban",
        f"**Banned User**\n\n**User:** {user.mention}\n**User ID:** `{user.id}`\n**Reason:** `{reason}`\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message(
    "unban",
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def unban(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await zelretch.delete(
            message, "𝖭𝖾𝖾𝖽 𝖺 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾/𝗂𝖽 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗎𝗌𝖾𝗋 𝗍𝗈 𝗎𝗇𝖻𝖺𝗇 𝗍𝗁𝖾𝗆!"
        )

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = await client.get_users(message.command[1])

    try:
        await message.chat.unban_member(user.id)
    except Exception as e:
        return await zelretch.error(message, e)

    await zelretch.delete(message, f"**🤗 𝖴𝗇𝖻𝖺𝗇𝗇𝖾𝖽 {user.mention} 𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒!**", 30)
    await zelretch.check_and_log(
        "unban",
        f"**Unbanned User**\n\n**User:** {user.mention}\n**User ID:** `{user.id}`\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message(
    ["kick", "dkick"],
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def kick(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if len(message.command) < 2:
            reason = None
        else:
            reason = await zelretch.input(message)
        if message.command[0][0].lower() == "d":
            try:
                await message.reply_to_message.delete()
            except Exception:
                pass
    elif len(message.command) == 2:
        user = await client.get_users(message.command[1])
        reason = None
    elif len(message.command) > 2:
        user = await client.get_users(message.command[1])
        reason = (await zelretch.input(message)).split(" ", 1)[1].strip()
    else:
        return await zelretch.delete(
            message, "𝖭𝖾𝖾𝖽 𝖺 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾/𝗂𝖽 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗎𝗌𝖾𝗋 𝗍𝗈 𝗄𝗂𝖼𝗄 𝗍𝗁𝖾𝗆!"
        )

    try:
        await message.chat.ban_member(user.id)
    except Exception as e:
        return await zelretch.error(message, e)

    reason = reason if reason else "Not Specified"
    await zelretch.delete(
        message,
        f"**👋 𝖪𝗂𝖼𝗄𝖾𝖽 {user.mention} 𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒!**\n**𝖱𝖾𝖺𝗌𝗈𝗇:** `{reason}`",
        30,
    )
    await zelretch.check_and_log(
        "kick",
        f"**Kicked User**\n\n**User:** {user.mention}\n**User ID:** `{user.id}`\n**Reason:** `{reason}`\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )
    await asyncio.sleep(5)
    try:
        await message.chat.unban_member(user.id)
    except Exception:
        pass


@on_message(
    "mute",
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def mute(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if len(message.command) < 2:
            reason = None
        else:
            reason = await zelretch.input(message)
    elif len(message.command) == 2:
        user = await client.get_users(message.command[1])
        reason = None
    elif len(message.command) > 2:
        user = await client.get_users(message.command[1])
        reason = (await zelretch.input(message)).split(" ", 1)[1].strip()
    else:
        return await zelretch.delete(
            message, "𝖭𝖾𝖾𝖽 𝖺 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾/𝗂𝖽 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗎𝗌𝖾𝗋 𝗍𝗈 𝗆𝗎𝗍𝖾 𝗍𝗁𝖾𝗆!"
        )

    try:
        permissions = ChatPermissions(
            can_send_messages=False,
        )
        await message.chat.restrict_member(user.id, permissions)
    except Exception as e:
        return await zelretch.error(message, e)

    reason = reason if reason else "Not Specified"
    await zelretch.delete(
        message,
        f"**🤐 𝖬𝗎𝗍𝖾𝖽 {user.mention} 𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒!**\n**𝖱𝖾𝖺𝗌𝗈𝗇:** `{reason}`",
        30,
    )
    await zelretch.check_and_log(
        "mute",
        f"**Muted User**\n\n**User:** {user.mention}\n**User ID:** `{user.id}`\n**Reason:** `{reason}`\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message(
    "unmute",
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def unmute(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await zelretch.delete(
            message, "𝖭𝖾𝖾𝖽 𝖺 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾/𝗂𝖽 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗎𝗌𝖾𝗋 𝗍𝗈 𝗎𝗇𝗆𝗎𝗍𝖾 𝗍𝗁𝖾𝗆!"
        )

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = await client.get_users(message.command[1])

    try:
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
        await message.chat.restrict_member(user.id, permissions)
    except Exception as e:
        return await zelretch.error(message, e)

    await zelretch.delete(message, f"**😁 𝖴𝗇𝗆𝗎𝗍𝖾𝖽 {user.mention} 𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒!**", 30)
    await zelretch.check_and_log(
        "unmute",
        f"**Unmuted User**\n\n**User:** {user.mention}\n**User ID:** `{user.id}`\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message("dmute", allow_master=True)
async def dmute(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if len(message.command) < 2:
            reason = None
        else:
            reason = await zelretch.input(message)
    elif len(message.command) == 2:
        user = await client.get_users(message.command[1])
        reason = None
    elif len(message.command) > 2:
        user = await client.get_users(message.command[1])
        reason = (await zelretch.input(message)).split(" ", 1)[1].strip()
    else:
        return await zelretch.delete(
            message, "𝖭𝖾𝖾𝖽 𝖺 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾/𝗂𝖽 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗎𝗌𝖾𝗋 𝗍𝗈 𝗆𝗎𝗍𝖾 𝗍𝗁𝖾𝗆!"
        )

    if await db.is_muted(client.me.id, user.id, message.chat.id):
        return await zelretch.delete(message, "This user is already dmuted.")

    reason = reason if reason else "Not Specified"
    await db.add_mute(client.me.id, user.id, message.chat.id, reason)
    await zelretch.delete(
        message,
        f"**🤐 𝖬𝗎𝗍𝖾𝖽 {user.mention} 𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒!**\n**𝖱𝖾𝖺𝗌𝗈𝗇:** `{reason}`",
        30,
    )
    await zelretch.check_and_log(
        "dmute",
        f"**D-Muted User**\n\n**User:** {user.mention}\n**User ID:** `{user.id}`\n**Reason:** `{reason}`\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title or message.chat.first_name}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message("undmute", allow_master=True)
async def undmute(client: Client, message: Message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await zelretch.delete(
            message, "𝖭𝖾𝖾𝖽 𝖺 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾/𝗂𝖽 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗎𝗌𝖾𝗋 𝗍𝗈 𝗎𝗇𝗆𝗎𝗍𝖾 𝗍𝗁𝖾𝗆!"
        )

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = await client.get_users(message.command[1])

    if not await db.is_muted(client.me.id, user.id, message.chat.id):
        return await zelretch.delete(message, "𝖳𝗁𝖾 𝗎𝗌𝖾𝗋 𝗂𝗌 𝗇𝗈𝗍 𝗆𝗎𝗍𝖾𝖽!")

    reason = await db.rm_mute(client.me.id, user.id, message.chat.id)
    await zelretch.delete(
        message,
        f"**😁 𝖴𝗇𝗆𝗎𝗍𝖾𝖽 {user.mention} 𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒!**\n\n**Mute reason was:** `{reason}`",
        30,
    )
    await zelretch.check_and_log(
        "unmute",
        f"**D-Unmuted User**\n\n**User:** {user.mention}\n**User ID:** `{user.id}`\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message(
    "pin",
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def pin(_, message: Message):
    if not message.reply_to_message:
        return await zelretch.delete(message, "𝖭𝖾𝖾𝖽 𝖺 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝗉𝗂𝗇 𝖺 𝗆𝖾𝗌𝗌𝖺𝗀𝖾!")

    try:
        await message.reply_to_message.pin()
    except Exception as e:
        return await zelretch.error(message, e)

    await zelretch.delete(
        message,
        f"**📌 𝖯𝗂𝗇𝗇𝖾𝖽 [𝖬𝖾𝗌𝗌𝖺𝗀𝖾]({message.reply_to_message.link}) 𝗂𝗇 {message.chat.title}!**",
        30,
    )
    await zelretch.check_and_log(
        "pin",
        f"**Pinned Message**\n\n**Message:** [Click Here]({message.reply_to_message.link})\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message(
    "unpin",
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def unpin(_, message: Message):
    if not message.reply_to_message:
        return await zelretch.delete(message, "𝖭𝖾𝖾𝖽 𝖺 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝗎𝗇𝗉𝗂𝗇 𝖺 𝗆𝖾𝗌𝗌𝖺𝗀𝖾!")

    try:
        await message.reply_to_message.unpin()
    except Exception as e:
        return await zelretch.error(message, e)

    await zelretch.delete(
        message,
        f"**📌 𝖴𝗇𝗉𝗂𝗇𝗇𝖾𝖽 [𝖬𝖾𝗌𝗌𝖺𝗀𝖾]({message.reply_to_message.link}) 𝗂𝗇 {message.chat.title}!**",
        30,
    )
    await zelretch.check_and_log(
        "unpin",
        f"**Unpinned Message**\n\n**Message:** [Click Here]({message.reply_to_message.link})\n**Admin:** `{message.from_user.mention}`\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`",
    )


@on_message(
    "zombies",
    chat_type=group_only,
    admin_only=True,
    allow_master=True,
)
async def zombies(_, message: Message):
    kaleido = await zelretch.edit(message, "☠️ 𝖣𝖾𝗍𝖾𝖼𝗍𝗂𝗇𝗀 𝗓𝗈𝗆𝖻𝗂𝖾𝗌...")
    ded_users = []
    async for members in message.chat.get_members():
        if members.user.is_deleted:
            ded_users.append(members.user.id)

    if not ded_users:
        return await kaleido.edit(
            "🫡 𝖣𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝖺𝗇𝗒 𝗓𝗈𝗆𝖻𝗂𝖾𝗌 𝗂𝗇 𝗍𝗁𝗂𝗌 𝗀𝗋𝗈𝗎𝗉. **𝖦𝗋𝗈𝗎𝗉𝗌' 𝖼𝗅𝖾𝖺𝗇 𝖠𝖥!**"
        )

    if len(message.command) > 1 and message.command[1].lower() == "clean":
        await kaleido.edit(
            f"☠️ 𝖥𝗈𝗎𝗇𝖽 {len(ded_users)} 𝗓𝗈𝗆𝖻𝗂𝖾𝗌... **🔫 𝖳𝗂𝗆𝖾 𝗍𝗈 𝗉𝗎𝗋𝗀𝖾 𝗍𝗁𝖾𝗆!**"
        )
        failed = 0
        success = 0
        for user in ded_users:
            try:
                await message.chat.ban_member(user)
                success += 1
            except Exception as e:
                LOGS.error(e)
                failed += 1

        await kaleido.edit(f"**𝖯𝗎𝗋𝗀𝖾𝖽 {success} 𝗓𝗈𝗆𝖻𝗂𝖾𝗌!**\n`{failed}` holds immunity!")
    else:
        await kaleido.edit(
            f"**☠️ 𝖥𝗈𝗎𝗇𝖽 {len(ded_users)} 𝗓𝗈𝗆𝖻𝗂𝖾𝗌!**\n\n__Use__ `{handler}zombies clean` __to kill them!__"
        )


@custom_handler(filters.incoming)
async def multiple_handler(client: Client, message: Message):
    if not message.from_user:
        return

    if await db.is_muted(client.me.id, message.from_user.id, message.chat.id):
        try:
            await message.delete()
        except:
            pass

    elif await db.is_gmuted(message.from_user.id):
        try:
            await message.delete()
        except:
            pass

    elif await db.is_echo(client.me.id, message.chat.id, message.from_user.id):
        await message.copy(message.chat.id, reply_to_message_id=message.id)


HelpMenu("admin").add(
    "promote",
    "<username/id/reply> <title (optional)>",
    "Promote a user to admin in the current chat. An optional custom title can be assigned.",
    "promote @ZelretchUser Workshop Keeper",
).add(
    "demote",
    "<username/id/reply>",
    "Remove admin privileges from a user in the current chat.",
    "demote @ZelretchUser",
).add(
    "ban",
    "<username/id/reply> <reason (optional)>",
    "Ban a user from the current chat. Use 'dban' to also delete their message.",
    "ban @ZelretchUser spamming",
    "Alias 'dban' deletes the replied message before banning.",
).add(
    "unban",
    "<username/id/reply>",
    "Lift a ban on a previously banned user.",
    "unban @ZelretchUser",
).add(
    "kick",
    "<username/id/reply> <reason (optional)>",
    "Remove a user from the chat. They can rejoin if they have an invite link.",
    "kick @ZelretchUser off-topic",
    "Alias 'dkick' deletes the replied message before kicking.",
).add(
    "mute",
    "<username/id/reply> <reason (optional)>",
    "Mute a user so they cannot send messages in the chat.",
    "mute @ZelretchUser excessive mentions",
    "Alias 'dmute' mutes and deletes their new messages automatically.",
).add(
    "unmute",
    "<username/id/reply>",
    "Restore a muted user's ability to send messages.",
    "unmute @ZelretchUser",
).add(
    "dmute",
    "<username/id/reply>",
    "Mute a user and automatically delete any new messages they send.",
    "dmute @ZelretchUser",
    "Requires delete message permission. Use 'undmute' to lift this restriction.",
).add(
    "undmute",
    "<username/id/reply>",
    "Lift a deletion-mute previously applied with 'dmute'.",
    "undmute @ZelretchUser",
).add(
    "pin",
    "<reply>",
    "Pin the replied message to the top of the chat.",
    "pin",
).add(
    "unpin",
    "<reply>",
    "Unpin the replied pinned message.",
    "unpin",
).add(
    "zombies",
    None,
    "Scan the chat for deleted (zombie) accounts. Pass 'clean' to also remove them.",
    "zombies clean",
).info(
    "Group administration commands. The userbot must be an admin with the appropriate rights for each command to work."
).done()

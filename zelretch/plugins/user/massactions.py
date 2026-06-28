import asyncio
import datetime
import time

from kurigram import Client
from kurigram.enums import ChatMembersFilter
from kurigram.errors import FloodWait
from kurigram.types import Message

from . import HelpMenu, group_n_channel, group_only, zelretch, on_message


@on_message("banall", chat_type=group_n_channel, admin_only=True, allow_master=True)
async def banall(client: Client, message: Message):
    chat_id = message.chat.id
    chat_name = message.chat.title
    if len(message.command) > 1:
        try:
            chat = await client.get_chat(message.command[1])
            chat_id = chat.id
            chat_name = chat.title
        except Exception as e:
            return await zelretch.error(message, f"__Invalid chatId.__\n\n`{e}`")

    ban_right = await client.get_chat_member(chat_id, client.me.id)
    if not (ban_right.privileges and ban_right.privileges.can_restrict_members):
        return await zelretch.delete(
            message,
            f"__I don't have enough rights to ban users in {chat_name}.__\n\n__Give me permission to ban users and try again.__",
        )

    kaleido = await zelretch.edit(message, f"__Banning all users in {chat_name}.__")

    total = 0
    success = 0
    async for users in client.get_chat_members(chat_id):
        total += 1
        try:
            await client.ban_chat_member(chat_id, users.user.id)
            success += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except Exception:
            pass

    await zelretch.delete(
        kaleido,
        f"Banall Executed! \n\n__Total:__ {total} \n__Banned:__ {success} \n__Failed:__ {total - success}",
    )
    await zelretch.check_and_log(
        "banall",
        f"**Banall In:** {chat_name} \n**Total:** {total} \n**Banned:** {success} \n**Failed:** {total - success}\n\n**By:** {client.me.mention}",
    )


@on_message("unbanall", chat_type=group_n_channel, admin_only=True, allow_master=True)
async def unbanall(client: Client, message: Message):
    chat_id = message.chat.id
    chat_name = message.chat.title

    if len(message.command) > 1:
        try:
            chat = await client.get_chat(message.command[1])
            chat_id = chat.id
            chat_name = chat.title
        except Exception as e:
            return await zelretch.error(message, f"__Invalid chatId.__\n\n`{e}`")

    ban_right = await client.get_chat_member(chat_id, client.me.id)
    if not (ban_right.privileges and ban_right.privileges.can_restrict_members):
        return await zelretch.delete(
            message,
            f"__I don't have enough rights to unban users in {chat_name}.__\n\n__Give me permission to ban users and try again.__",
        )

    kaleido = await zelretch.edit(message, f"__Unbanning all users in {chat_name}.__")

    total = 0
    success = 0
    async for users in client.get_chat_members(
        chat_id, filter=ChatMembersFilter.BANNED
    ):
        total += 1
        try:
            await client.unban_chat_member(chat_id, users.user.id)
            success += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except Exception:
            pass

    await zelretch.delete(
        kaleido,
        f"Unbanall Executed! \n\n__Total:__ {total} \n__Unbanned:__ {success} \n__Failed:__ {total - success}",
    )
    await zelretch.check_and_log(
        "unbanall",
        f"**Unbanall In:** {chat_name} \n**Total:** {total} \n**Unbanned:** {success} \n**Failed:** {total - success}\n\n**By:** {client.me.mention}",
    )


@on_message("kickall", chat_type=group_n_channel, admin_only=True, allow_master=True)
async def kickall(client: Client, message: Message):
    chat_id = message.chat.id
    chat_name = message.chat.title
    if len(message.command) > 1:
        try:
            chat = await client.get_chat(message.command[1])
            chat_id = chat.id
            chat_name = chat.title
        except Exception as e:
            return await zelretch.error(message, f"__Invalid chatId.__\n\n`{e}`")

    ban_right = await client.get_chat_member(chat_id, client.me.id)
    if not (ban_right.privileges and ban_right.privileges.can_restrict_members):
        return await zelretch.delete(
            message,
            f"__I don't have enough rights to kick users in {chat_name}.__\n\n__Give me permission to ban users and try again.__",
        )

    kaleido = await zelretch.edit(message, f"__Kicking all users in {chat_name}.__")

    total = 0
    success = 0
    async for users in client.get_chat_members(chat_id):
        total += 1
        try:
            await client.ban_chat_member(
                chat_id,
                users.user.id,
                datetime.datetime.fromtimestamp(time.time() + 45),
            )
            success += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except Exception:
            pass

    await zelretch.delete(
        kaleido,
        f"Kickall Executed! \n\n__Total:__ {total} \n__Kicked:__ {success} \n__Failed:__ {total - success}",
    )
    await zelretch.check_and_log(
        "kickall",
        f"**Kickall In:** {chat_name} \n**Total:** {total} \n**Kicked:** {success} \n**Failed:** {total - success}\n\n**By:** {client.me.mention}",
    )


@on_message(
    ["deleteall", "delall"], chat_type=group_only, admin_only=True, allow_master=True
)
async def deleteall(client: Client, message: Message):
    if not message.reply_to_message:
        return await zelretch.delete(
            message, "__Reply to a message to delete all messages from that user.__"
        )

    kaleido = await zelretch.edit(message, "__Deleting all messages from this user.__")
    target = message.reply_to_message.from_user
    if not target:
        return await zelretch.delete(message, "Can't identify that user.")
    user = target.id

    await client.delete_user_history(message.chat.id, user)
    await zelretch.delete(kaleido, "__All messages from this user has been deleted.__")


@on_message("blockall", chat_type=group_only, allow_master=True)
async def blockall(client: Client, message: Message):
    chat_id = message.chat.id
    chat_name = message.chat.title

    if len(message.command) > 1:
        try:
            chat = await client.get_chat(message.command[1])
            chat_id = chat.id
            chat_name = chat.title
        except Exception as e:
            return await zelretch.error(message, f"__Invalid chatId.__\n\n`{e}`")

    kaleido = await zelretch.edit(message, f"__Kicking all users in {chat_name}.__")

    total = 0
    success = 0
    async for users in client.get_chat_members(chat_id):
        total += 1
        try:
            await client.block_user(users.user.id)
            success += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except Exception:
            pass

    await zelretch.edit(
        kaleido,
        f"__Blockall Executed!__ \n\n__Total:__ {total} \n__Blocked:__ {success} \n__Failed:__ {total - success}",
    )
    await zelretch.check_and_log(
        "blockall",
        f"**Blockall In:** {chat_name} \n**Total:** {total} \n**Blocked:** {success} \n**Failed:** {total - success}\n\n**By:** {client.me.mention}",
    )


@on_message("unblockall", chat_type=group_only, allow_master=True)
async def unblockall(client: Client, message: Message):
    chat_id = message.chat.id
    chat_name = message.chat.title

    if len(message.command) > 1:
        try:
            chat = await client.get_chat(message.command[1])
            chat_id = chat.id
            chat_name = chat.title
        except Exception as e:
            return await zelretch.error(message, f"__Invalid chatId.__\n\n`{e}`")

    kaleido = await zelretch.edit(message, f"__Unblocking all users in {chat_name}.__")

    total = 0
    success = 0
    async for users in client.get_chat_members(chat_id):
        total += 1
        try:
            await client.unblock_user(users.user.id)
            success += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except Exception:
            pass

    await zelretch.edit(
        kaleido,
        f"__Unblockall Executed!__ \n\n__Total:__ {total} \n__Unblocked:__ {success} \n__Failed:__ {total - success}",
    )
    await zelretch.check_and_log(
        "unblockall",
        f"**Unblockall In:** {chat_name} \n**Total:** {total} \n**Unblocked:** {success} \n**Failed:** {total - success}\n\n**By:** {client.me.mention}",
    )


@on_message("inviteall", allow_master=True)
async def inviteAll(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give a chatId from where to invite all users.")

    try:
        from_chat = await client.get_chat(message.command[1])
    except Exception as e:
        return await zelretch.error(message, f"`{e}`")

    to_chat = message.chat
    targets = []
    if from_chat.id == -1001641358740:
        return await zelretch.delete(message, "Can't add members from this chat!")

    async for users in client.get_chat_members(from_chat.id, limit=200):
        if users.user.is_bot:
            continue
        if users.user.is_deleted:
            continue

        targets.append(users.user.id)

    try:
        await to_chat.add_members(targets)
    except Exception as e:
        return await zelretch.error(message, f"`{e}`")

    await zelretch.delete(message, f"__Added {len(targets)} users to {to_chat.title}.__")


HelpMenu("massactions").add(
    "banall",
    "<chat id (optional)>",
    "Ban every member of a group or channel. If no chat id is given, the action runs against the current chat.",
    "banall -1001234567890",
    "The userbot must be an admin with ban permission in the target chat.",
).add(
    "unbanall",
    "<chat id (optional)>",
    "Lift every ban in a group or channel at once. If no chat id is given, the action runs against the current chat.",
    "unbanall -1001234567890",
).add(
    "kickall",
    "<chat id (optional)>",
    "Remove every member from a group or channel. If no chat id is given, the action runs against the current chat.",
    "kickall -1001234567890",
).add(
    "deleteall",
    None,
    "Delete every message sent by the replied user in the current chat. Reply to one of the target user's messages first.",
    "deleteall",
    "Alias 'delall' can also be used.",
).add(
    "blockall",
    "<chat id (optional)>",
    "Block every member of a group or channel from contacting the userbot account. If no chat id is given, the action runs against the current chat.",
    "blockall -1001234567890",
).add(
    "unblockall",
    "<chat id (optional)>",
    "Unblock every member of a group or channel. If no chat id is given, the action runs against the current chat.",
    "unblockall -1001234567890",
).add(
    "inviteall",
    "<source chat id>",
    "Invite every member from the source chat into the current chat via invite links.",
    "inviteall -1001234567890",
    "Use with extreme caution. Mass-inviting users can trigger Telegram's anti-spam systems and get the userbot account restricted or banned.",
).info(
    "Bulk administrative actions — ban, unban, kick, block, unblock, invite, or delete across an entire chat at once."
).done()

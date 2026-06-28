from kurigram import Client
from kurigram.enums import ChatType
from kurigram.types import ChatPermissions, Message

from . import HelpMenu, Symbols, zelretch, on_message


@on_message("lock", admin_only=True, allow_master=True)
async def lockGC(client: Client, message: Message):
    if not message.chat.type == ChatType.SUPERGROUP:
        return await zelretch.delete(message, "Only supergroups are supported.")

    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me something to lock.")

    lock_type = message.command[1].lower()

    if len(message.command) > 2:
        time_data = message.command[2]
        try:
            if "d" in time_data:
                mtime = int(time_data.split("d")[0].strip()) * 24 * 60 * 60
            elif "h" in time_data:
                mtime = int(time_data.split("h")[0].strip()) * 60 * 60
            elif "m" in time_data:
                mtime = int(time_data.split("m")[0].strip()) * 60
            else:
                return await zelretch.delete(message, "Invalid duration format. Use xd, xh, or xm.")
        except ValueError:
            return await zelretch.delete(message, "Duration must be a number. Use xd, xh, or xm.")
    else:
        mtime = 0
        time_data = "forever"

    if lock_type == "all":
        perms = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_add_web_page_previews=False,
            can_send_other_messages=False,
            can_send_polls=False,
        )
    elif lock_type == "messages":
        perms = ChatPermissions(can_send_messages=False)
    elif lock_type == "media":
        perms = ChatPermissions(can_send_media_messages=False)
    elif lock_type == "info":
        perms = ChatPermissions(can_change_info=False)
    elif lock_type == "invites":
        perms = ChatPermissions(can_invite_users=False)
    elif lock_type == "pin":
        perms = ChatPermissions(can_pin_messages=False)
    elif lock_type in ["gif", "sticker", "games", "inline"]:
        perms = ChatPermissions(can_send_other_messages=False)
    elif lock_type == "polls":
        perms = ChatPermissions(can_send_polls=False)
    elif lock_type == "url":
        perms = ChatPermissions(can_add_web_page_previews=False)
    else:
        return await zelretch.delete(message, "Invalid lock type.")

    await client.set_chat_permissions(message.chat.id, perms)

    await zelretch.edit(
        message,
        f"**Locked {lock_type} for {message.chat.title}**\n\n**Duration:** `{time_data}`",
    )


@on_message("unlock", admin_only=True, allow_master=True)
async def unlockGC(client: Client, message: Message):
    if not message.chat.type == ChatType.SUPERGROUP:
        return await zelretch.delete(message, "Only supergroups are supported.")

    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me something to unlock.")

    lock_type = message.command[1].lower()

    if lock_type == "all":
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_add_web_page_previews=True,
            can_send_polls=True,
            can_send_other_messages=True,
        )
    elif lock_type == "messages":
        perms = ChatPermissions(can_send_messages=True)
    elif lock_type == "media":
        perms = ChatPermissions(can_send_media_messages=True)
    elif lock_type == "info":
        perms = ChatPermissions(can_change_info=True)
    elif lock_type == "invites":
        perms = ChatPermissions(can_invite_users=True)
    elif lock_type == "pin":
        perms = ChatPermissions(can_pin_messages=True)
    elif lock_type in ["gif", "sticker", "games", "inline"]:
        perms = ChatPermissions(can_send_other_messages=True)
    elif lock_type == "polls":
        perms = ChatPermissions(can_send_polls=True)
    elif lock_type == "url":
        perms = ChatPermissions(can_add_web_page_previews=True)
    else:
        return await zelretch.delete(message, "Invalid lock type.")

    await client.set_chat_permissions(message.chat.id, perms)

    await zelretch.edit(message, f"**Unlocked {lock_type} for {message.chat.title}**")


@on_message("locktypes", allow_master=True)
async def lockTypes(_, message: Message):
    await zelretch.edit(
        message,
        "**Lock Types:**\n\n"
        f"{Symbols.triangle_right} `all` - __Locks all permissions__\n"
        f"{Symbols.triangle_right} `messages` - __Locks sending messages__\n"
        f"{Symbols.triangle_right} `media` - __Locks sending media__\n"
        f"{Symbols.triangle_right} `info` - __Locks changing group info__\n"
        f"{Symbols.triangle_right} `invites` - __Locks inviting users__\n"
        f"{Symbols.triangle_right} `pin` - __Locks pinning messages__\n"
        f"{Symbols.triangle_right} `gif` - __Locks sending gifs__\n"
        f"{Symbols.triangle_right} `sticker` - __Locks sending stickers__\n"
        f"{Symbols.triangle_right} `games` - __Locks sending games__\n"
        f"{Symbols.triangle_right} `inline` - __Locks sending inline results__\n"
        f"{Symbols.triangle_right} `polls` - __Locks sending polls__\n"
        f"{Symbols.triangle_right} `url` - __Locks sending urls__\n",
    )


HelpMenu("locker").add(
    "lock",
    "<lock type> <duration (optional)>",
    "Restrict a specific type of message (or all messages) in the current chat. The userbot must be an admin with restrict-member permission.",
    "lock stickers 2d",
    "Duration is optional. Use 'xd' (days), 'xh' (hours), or 'xm' (minutes). Use 'all' as the lock type to lock every permission at once.",
).add(
    "unlock",
    "<lock type>",
    "Restore a previously locked message type, or use 'all' to unlock every permission at once.",
    "unlock stickers",
).add(
    "locktypes",
    None,
    "List every lockable chat permission supported by the bot (messages, media, stickers, polls, etc.).",
    "locktypes",
).info(
    "Lock and unlock chat permissions — control which message types members are allowed to send."
).done()

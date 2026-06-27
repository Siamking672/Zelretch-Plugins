import random

from kurigram import Client
from kurigram.enums import ChatMembersFilter, ChatMemberStatus
from kurigram.types import Message

from zelretch.functions.media import get_media_fileid
from zelretch.functions.templates import chat_info_templates

from . import HelpMenu, group_n_channel, zelretch, on_message

kickme_quotes = [
    "✌️ 𝖮𝗎𝗍𝗍𝖺 𝗁𝖾𝗋𝖾, 𝗅𝖾𝖺𝗏𝗂𝗇𝗀 𝗍𝗁𝖾 𝗌𝗍𝖺𝗀𝖾 𝗍𝗈 𝗍𝗁𝖾 𝗋𝖾𝖺𝗅 𝗌𝗍𝖺𝗋𝗌!",
    "🚀 𝖤𝗅𝖾𝗏𝖺𝗍𝗂𝗇𝗀 𝗆𝗒 𝗏𝗂𝖻𝖾𝗌, 𝗅𝖾𝖺𝗏𝗂𝗇𝗀 𝗍𝗁𝖾 𝖼𝗁𝖺𝗍 𝗂𝗇 𝗌𝗍𝗒𝗅𝖾.",
    "🕊️ 𝖥𝗅𝗒𝗂𝗇𝗀 𝗌𝗈𝗅𝗈, 𝖾𝗑𝗂𝗍𝗂𝗇𝗀 𝗍𝗁𝗂𝗌 𝗀𝗋𝗈𝗎𝗉 𝗀𝗋𝖺𝖼𝖾𝖿𝗎𝗅𝗅𝗒.",
    "🌪️ 𝖲𝗍𝗂𝗋𝗋𝗂𝗇𝗀 𝗎𝗉 𝗍𝗁𝖾 𝗐𝗂𝗇𝖽𝗌 𝗈𝖿 𝖽𝖾𝗉𝖺𝗋𝗍𝗎𝗋𝖾, 𝖻𝗒𝖾!",
    "🚶‍♂️ 𝖶𝖺𝗅𝗄𝗂𝗇𝗀 𝖺𝗐𝖺𝗒 𝗅𝗂𝗄𝖾 𝖺 𝖻𝗈𝗌𝗌, 𝗌𝖾𝖾 𝗒𝗈𝗎 𝗇𝖾𝗏𝖾𝗋!",
    "🔥 𝖡𝗎𝗋𝗇𝗂𝗇𝗀 𝖻𝗋𝗂𝖽𝗀𝖾𝗌 𝖺𝗇𝖽 𝖼𝗋𝖾𝖺𝗍𝗂𝗇𝗀 𝗆𝗒 𝗈𝗐𝗇 𝗉𝖺𝗍𝗁. 𝖠𝖽𝗂𝗈𝗌!",
    "💫 𝖳𝗎𝗋𝗇𝗂𝗇𝗀 𝗍𝗁𝖾 𝗉𝖺𝗀𝖾 𝖺𝗇𝖽 𝖼𝗅𝗈𝗌𝗂𝗇𝗀 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗉𝗍𝖾𝗋.",
    "👑 𝖢𝗋𝗈𝗐𝗇'𝗌 𝗍𝗈𝗈 𝗁𝖾𝖺𝗏𝗒 𝖿𝗈𝗋 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍. 𝖨'𝗆 𝗈𝗎𝗍!",
    "🏃‍♂️ 𝖲𝗉𝗋𝗂𝗇𝗍𝗂𝗇𝗀 𝗈𝗎𝗍 𝗈𝖿 𝗁𝖾𝗋𝖾 𝗐𝗂𝗍𝗁 𝖿𝗅𝖺𝗂𝗋. 𝖢𝖺𝗍𝖼𝗁 𝗒𝗈𝗎 𝗇𝖾𝗏𝖾𝗋!",
    "🚤 𝖲𝖺𝗂𝗅𝗂𝗇𝗀 𝖺𝗐𝖺𝗒 𝖿𝗋𝗈𝗆 𝗍𝗁𝗂𝗌 𝗀𝗋𝗈𝗎𝗉 𝖼𝗁𝖺𝗍, 𝗌𝗆𝗈𝗈𝗍𝗁 𝗌𝖾𝖺𝗌 𝖺𝗁𝖾𝖺𝖽!",
    "🍃 𝖫𝗂𝗄𝖾 𝖺 𝗅𝖾𝖺𝖿 𝗂𝗇 𝗍𝗁𝖾 𝗐𝗂𝗇𝖽, 𝖨'𝗆 𝖽𝗋𝗂𝖿𝗍𝗂𝗇𝗀 𝖺𝗐𝖺𝗒. 𝖥𝖺𝗋𝖾𝗐𝖾𝗅𝗅!",
    "🛫 𝖳𝖺𝗄𝗂𝗇𝗀 𝗈𝖿𝖿 𝖿𝗋𝗈𝗆 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍 𝗋𝗎𝗇𝗐𝖺𝗒. 𝖡𝗈𝗇 𝗏𝗈𝗒𝖺𝗀𝖾!",
    "💼 𝖢𝗅𝗈𝗌𝗂𝗇𝗀 𝗍𝗁𝖾 𝖻𝗋𝗂𝖾𝖿𝖼𝖺𝗌𝖾 𝗈𝗇 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍. 𝖯𝗋𝗈𝖿𝖾𝗌𝗌𝗂𝗈𝗇𝖺𝗅 𝖾𝗑𝗂𝗍!",
    "🎭 𝖤𝗑𝗂𝗍𝗂𝗇𝗀 𝗍𝗁𝖾 𝗌𝗍𝖺𝗀𝖾 𝗐𝗂𝗍𝗁 𝖺 𝖽𝗋𝖺𝗆𝖺𝗍𝗂𝖼 𝖿𝗅𝖺𝗂𝗋. 𝖳𝖺-𝖽𝖺!",
    "🎶 𝖯𝗅𝖺𝗒𝗂𝗇𝗀 𝗆𝗒 𝖾𝗑𝗂𝗍 𝗆𝗎𝗌𝗂𝖼. 𝖢𝗎𝖾 𝗍𝗁𝖾 𝖿𝖺𝗋𝖾𝗐𝖾𝗅𝗅 𝗌𝗒𝗆𝗉𝗁𝗈𝗇𝗒!",
    "🕶️ 𝖥𝖺𝖽𝗂𝗇𝗀 𝗂𝗇𝗍𝗈 𝗍𝗁𝖾 𝗌𝗁𝖺𝖽𝗈𝗐𝗌, 𝗅𝖾𝖺𝗏𝗂𝗇𝗀 𝖺𝗇 𝖺𝗂𝗋 𝗈𝖿 𝗆𝗒𝗌𝗍𝖾𝗋𝗒.",
    "🚪 𝖢𝗅𝗈𝗌𝗂𝗇𝗀 𝗍𝗁𝖾 𝖽𝗈𝗈𝗋 𝗊𝗎𝗂𝖾𝗍𝗅𝗒 𝗈𝗇 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍. 𝖤𝗑𝗂𝗍 𝖼𝗈𝗆𝗉𝗅𝖾𝗍𝖾!",
    "🔒 𝖫𝗈𝖼𝗄𝗂𝗇𝗀 𝗍𝗁𝖾 𝖼𝗁𝖺𝗍 𝖻𝖾𝗁𝗂𝗇𝖽 𝗆𝖾. 𝖪𝖾𝖾𝗉 𝗂𝗍 𝗌𝗍𝗒𝗅𝗂𝗌𝗁, 𝖿𝗈𝗅𝗄𝗌!",
    "🌌 𝖵𝖺𝗇𝗂𝗌𝗁𝗂𝗇𝗀 𝗂𝗇𝗍𝗈 𝗍𝗁𝖾 𝖼𝗈𝗌𝗆𝗂𝖼 𝖺𝖻𝗒𝗌𝗌. 𝖲𝖾𝖾 𝗒𝗈𝗎 𝗂𝗇 𝗍𝗁𝖾 𝗌𝗍𝖺𝗋𝗌!",
    "💔 𝖡𝗋𝖾𝖺𝗄𝗂𝗇𝗀 𝖿𝗋𝖾𝖾 𝖿𝗋𝗈𝗆 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍. 𝖴𝗇𝗅𝖾𝖺𝗌𝗁𝗂𝗇𝗀 𝗆𝗒 𝗌𝗈𝗅𝗈 𝗃𝗈𝗎𝗋𝗇𝖾𝗒!",
    "👑 𝖤𝗑𝗂𝗍𝗂𝗇𝗀 𝗀𝗋𝖺𝖼𝖾𝖿𝗎𝗅𝗅𝗒. 𝖳𝗁𝗂𝗌 𝖼𝗁𝖺𝗍 𝖼𝗈𝗎𝗅𝖽𝗇'𝗍 𝗁𝖺𝗇𝖽𝗅𝖾 𝗆𝗒 𝗌𝗍𝗒𝗅𝖾.",
    "🚀 𝖳𝗂𝗆𝖾 𝖿𝗈𝗋 𝗆𝖾 𝗍𝗈 𝖻𝗅𝖺𝗌𝗍 𝗈𝖿𝖿. 𝖠𝖽𝗂𝗈𝗌, 𝖺𝗆𝗂𝗀𝗈𝗌!",
    "🌪️ 𝖲𝗍𝗂𝗋𝗋𝗂𝗇𝗀 𝗎𝗉 𝗍𝗁𝖾 𝖽𝗋𝖺𝗆𝖺 𝖺𝗇𝖽 𝗆𝖺𝗄𝗂𝗇𝗀 𝗆𝗒 𝖾𝗑𝗂𝗍.",
]


@on_message(
    "setgpic",
    chat_type=group_n_channel,
    admin_only=True,
    allow_master=True,
)
async def setgpic(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await zelretch.delete(
            message, "𝖱𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗉𝗁𝗈𝗍𝗈 𝗍𝗈 𝗌𝖾𝗍 𝖺𝗌 𝗀𝗋𝗈𝗎𝗉 𝗉𝗋𝗈𝖿𝗂𝗅𝖾 𝗉𝗂𝖼𝗍𝗎𝗋𝖾."
        )

    status = await message.chat.set_photo(photo=message.reply_to_message.photo.file_id)
    if not status:
        return await zelretch.delete(message, "𝖲𝗈𝗋𝗋𝗒, 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝗐𝖾𝗇𝗍 𝗐𝗋𝗈𝗇𝗀.")

    await zelretch.delete(message, "𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒 𝗌𝖾𝗍 𝗀𝗋𝗈𝗎𝗉 𝗉𝗋𝗈𝖿𝗂𝗅𝖾 𝗉𝗂𝖼𝗍𝗎𝗋𝖾.")
    await zelretch.check_and_log(
        "setgpic",
        f"**Group Profile Picture**\n\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`\n**Admin:** `{message.from_user.mention}`",
    )


@on_message(
    "setgtitle",
    chat_type=group_n_channel,
    admin_only=True,
    allow_master=True,
)
async def setgtitle(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(
            message, "𝖨 𝗇𝖾𝖾𝖽 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝗍𝗈 𝗌𝖾𝗍 𝗍𝗁𝗂𝗌 𝗀𝗋𝗈𝗎𝗉 𝗍𝗂𝗍𝗅𝖾."
        )

    prev_title = message.chat.title
    new_title = await zelretch.input(message)
    status = await message.chat.set_title(new_title)
    if not status:
        return await zelretch.delete(message, "𝖲𝗈𝗋𝗋𝗒, 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝗐𝖾𝗇𝗍 𝗐𝗋𝗈𝗇𝗀.")

    await zelretch.delete(message, "𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒 𝗌𝖾𝗍 𝗀𝗋𝗈𝗎𝗉 𝗍𝗂𝗍𝗅𝖾.")
    await zelretch.check_and_log(
        "setgtitle",
        f"**Group Title**\n\n**Group:** `{prev_title}`\n**Group ID:** `{message.chat.id}`\n**Admin:** `{message.from_user.mention}`",
    )


@on_message(
    "setgabout",
    chat_type=group_n_channel,
    admin_only=True,
    allow_master=True,
)
async def setgabout(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(
            message, "𝖨 𝗇𝖾𝖾𝖽 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝗍𝗈 𝗌𝖾𝗍 𝗍𝗁𝗂𝗌 𝗀𝗋𝗈𝗎𝗉 𝖺𝖻𝗈𝗎𝗍."
        )

    new_about = await zelretch.input(message)
    status = await message.chat.set_description(new_about)
    if not status:
        return await zelretch.delete(message, "𝖲𝗈𝗋𝗋𝗒, 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝗐𝖾𝗇𝗍 𝗐𝗋𝗈𝗇𝗀.")

    await zelretch.delete(message, "𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒 𝗌𝖾𝗍 𝗀𝗋𝗈𝗎𝗉 𝖺𝖻𝗈𝗎𝗍.")
    await zelretch.check_and_log(
        "setgabout",
        f"**Group About**\n\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`\n**Admin:** `{message.from_user.mention}`",
    )


@on_message(
    "setgusername",
    chat_type=group_n_channel,
    admin_only=True,
    allow_master=True,
)
async def setgusername(client: Client, message: Message):
    user_status = (await message.chat.get_member(message.from_user.id)).status
    if user_status != ChatMemberStatus.OWNER:
        return await zelretch.delete(message, "𝖨 𝖺𝗆 𝗇𝗈𝗍 𝗍𝗁𝖾 𝗈𝗐𝗇𝖾𝗋 𝗈𝖿 𝗍𝗁𝗂𝗌 𝗀𝗋𝗈𝗎𝗉.")

    if len(message.command) < 2:
        return await zelretch.delete(
            message, "𝖨 𝗇𝖾𝖾𝖽 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝗍𝗈 𝗌𝖾𝗍 𝗍𝗁𝗂𝗌 𝗀𝗋𝗈𝗎𝗉'𝗌 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾."
        )

    new_username = await zelretch.input(message)
    status = await client.set_chat_username(message.chat.id, new_username)
    if not status:
        return await zelretch.delete(message, "𝖲𝗈𝗋𝗋𝗒, 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝗐𝖾𝗇𝗍 𝗐𝗋𝗈𝗇𝗀.")

    await zelretch.delete(message, "𝖲𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒 𝗌𝖾𝗍 𝗀𝗋𝗈𝗎𝗉 𝗎𝗌𝖾𝗋𝗇𝖺𝗆𝖾.")
    await zelretch.check_and_log(
        "setgusername",
        f"**Group Username**\n\n**Group:** `{message.chat.title}`\n**Group ID:** `{message.chat.id}`\n**Admin:** `{message.from_user.mention}`",
    )


@on_message(
    "getglink",
    chat_type=group_n_channel,
    admin_only=True,
    allow_master=True,
)
async def getglink(_, message: Message):
    link = await message.chat.export_invite_link()
    await zelretch.delete(message, f"**𝖦𝗋𝗈𝗎𝗉 𝗅𝗂𝗇𝗄:** `{link}`")


@on_message("kickme", chat_type=group_n_channel, allow_master=True)
async def kickme(client: Client, message: Message):
    kaleido = await zelretch.edit(message, random.choice(kickme_quotes))
    try:
        await client.leave_chat(message.chat.id)
    except Exception as e:
        return await zelretch.delete(
            kaleido, f"Deym! Can't leave this chat.\n**Error:** `{e}`"
        )


@on_message("newgroup", allow_master=True)
async def new_group(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "𝖨 𝗇𝖾𝖾𝖽 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝗍𝗈 𝗌𝖾𝗍 𝖺𝗌 𝗀𝗋𝗈𝗎𝗉 𝗍𝗂𝗍𝗅𝖾.")

    new_title = await zelretch.input(message)

    try:
        new_group = await client.create_group(new_title, zelretch.bot.me.id)
        await zelretch.edit(
            message, f"**𝖦𝗋𝗈𝗎𝗉 𝗅𝗂𝗇𝗄:** [{new_group.title}]({new_group.invite_link})"
        )
    except Exception as e:
        await zelretch.error(message, f"`{e}`", 20)


@on_message("newchannel", allow_master=True)
async def new_channel(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(
            message, "𝖨 𝗇𝖾𝖾𝖽 𝗌𝗈𝗆𝖾𝗍𝗁𝗂𝗇𝗀 𝗍𝗈 𝗌𝖾𝗍 𝖺𝗌 𝖼𝗁𝖺𝗇𝗇𝖾𝗅 𝗍𝗂𝗍𝗅𝖾."
        )

    new_title = await zelretch.input(message)

    try:
        new_channel = await client.create_channel(new_title, "Created by Zelretch")
        await zelretch.edit(
            message, f"**𝖢𝗁𝖺𝗇𝗇𝖾𝗅 𝗅𝗂𝗇𝗄:** [{new_channel.title}]({new_channel.username})"
        )
    except Exception as e:
        await zelretch.error(message, f"`{e}`", 20)


@on_message("chatinfo", allow_master=True)
async def chatInfo(client: Client, message: Message):
    if len(message.command) > 1:
        try:
            chat = await client.get_chat(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{e}`")
    else:
        chat = message.chat

    kaleido = await zelretch.edit(message, "Fetching chat info...")

    if chat.invite_link:
        chat_link = f"[Invite Link]({chat.invite_link})"
    elif chat.username:
        chat_link = f"@{chat.username}"
    else:
        chat_link = "Private Chat"

    chat_owner = None
    admins_count = 0
    bots_count = 0

    async for admin in client.get_chat_members(
        chat.id, filter=ChatMembersFilter.ADMINISTRATORS
    ):
        admins_count += 1
        if admin.status == ChatMemberStatus.OWNER:
            chat_owner = admin.user.mention

    async for _ in client.get_chat_members(chat.id, filter=ChatMembersFilter.BOTS):
        bots_count += 1

    chat_info = await chat_info_templates(
        chatName=chat.title,
        chatId=chat.id,
        chatLink=chat_link,
        chatOwner=chat_owner,
        dcId=chat.dc_id,
        membersCount=chat.members_count,
        adminsCount=admins_count,
        botsCount=bots_count,
        description=chat.description,
    )

    if chat.photo:
        async for photo in client.get_chat_photos(chat.id, 1):
            await kaleido.delete()
            await client.send_photo(
                message.chat.id,
                photo.file_id,
                caption=chat_info,
                reply_to_message_id=message.id,
                disable_notification=True,
            )
            return
    else:
        await kaleido.edit(chat_info, disable_web_page_preview=True)


@on_message("chatadmins", allow_master=True)
async def chatAdmins(client: Client, message: Message):
    if len(message.command) < 2:
        chat = message.chat
    else:
        try:
            chat = await client.get_chat(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{e}`")

    kaleido = await zelretch.edit(message, "Fetching chat admins...")

    admin_count = 0
    admins = "**💫 𝖠𝖽𝗆𝗂𝗇𝗌 𝗂𝗇 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍:**\n\n"
    async for admin in client.get_chat_members(
        chat.id, filter=ChatMembersFilter.ADMINISTRATORS
    ):
        admin_count += 1
        admins += f"**{'0' if admin_count < 10 else ''}{admin_count}:** {admin.user.mention} - `{admin.status}`\n"

    await kaleido.edit(admins, disable_web_page_preview=True)


@on_message("chatbots", allow_master=True)
async def chatBots(client: Client, message: Message):
    if len(message.command) < 2:
        chat = message.chat
    else:
        try:
            chat = await client.get_chat(message.command[1])
        except Exception as e:
            return await zelretch.error(message, f"`{e}`")

    kaleido = await zelretch.edit(message, "Fetching chat bots...")

    bot_count = 0
    bots = "**🤖 𝖡𝗈𝗍𝗌 𝗂𝗇 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍:**\n\n"
    async for bot in client.get_chat_members(chat.id, filter=ChatMembersFilter.BOTS):
        bot_count += 1
        bots += (
            f"**{'0' if bot_count < 10 else ''}{bot_count}:** @{bot.user.username}\n"
        )

    await kaleido.edit(bots, disable_web_page_preview=True)


@on_message("id", allow_master=True)
async def chatId(_, message: Message):
    if message.reply_to_message:
        msg = message.reply_to_message
    else:
        msg = message

    kaleido = await zelretch.edit(message, "Fetching message info...")

    info = f"**💫 ChatID:** `{msg.chat.id}`\n"
    info += f"**🪪 MessageID:** `{msg.id}`\n\n"

    if msg.from_user:
        info += f"**👤 UserID:** `{msg.from_user.id}`\n\n"

    if msg.forward_from:
        info += f"**👤 Forwarded From:** `{msg.forward_from.id}`\n\n"

    if msg.forward_from_chat:
        info += f"**💫 Forwarded ChatID:** `{msg.forward_from_chat.id}`\n\n"

    file_id = await get_media_fileid(msg)
    if file_id:
        info += f"**📁 FileID:** `{file_id}`\n\n"

    await kaleido.edit(info, disable_web_page_preview=True)


@on_message("invite", allow_master=True)
async def inviteUser(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(
            message, "I need a username/id to invite to this chat."
        )

    users = (await zelretch.input(message)).split(" ")
    kaleido = await zelretch.edit(message, "Inviting users...")

    resolved_users = await client.get_users(users)
    await message.chat.add_members([user.id for user in resolved_users])

    await kaleido.edit("Successfully invited users to this chat.")


HelpMenu("groups").add(
    "setgpic",
    "<reply to photo>",
    "Set the replied photo as the group's profile picture. The userbot must be an admin with the change chat photo permission.",
    "setgpic",
).add(
    "setgtitle",
    "<title>",
    "Change the title (name) of the current group or channel.",
    "setgtitle Workshop",
).add(
    "setgabout",
    "<text>",
    "Update the description (about) text of the current group or channel.",
    "setgabout A workshop for Mystic Codes",
).add(
    "setgusername",
    "<username>",
    "Set or change the public username of the current chat. Provide the username without the leading '@'.",
    "setgusername Zelretch",
    "Only group owners can use this command.",
).add(
    "getglink",
    None,
    "Generate and show the primary invite link for the current chat.",
    "getglink",
).add(
    "kickme",
    None,
    "Leave the current chat immediately, accompanied by a random farewell line.",
    "kickme",
).add(
    "newgroup",
    "<title>",
    "Create a brand new Telegram group with the given title. The userbot becomes the owner.",
    "newgroup Workshop",
).add(
    "newchannel",
    "<title>",
    "Create a brand new Telegram broadcast channel with the given title. The userbot becomes the owner.",
    "newchannel Workshop Announcements",
).add(
    "chatinfo",
    "<chat id/username (optional)>",
    "Display detailed information about a chat — title, type, member count, username, and description. Defaults to the current chat.",
    "chatinfo",
).add(
    "chatadmins",
    "<chat id/username (optional)>",
    "List every administrator of a chat along with their custom titles and permissions. Defaults to the current chat.",
    "chatadmins @Zelretch_Chats",
).add(
    "chatbots",
    "<chat id/username (optional)>",
    "List every bot that is a member of a chat. Defaults to the current chat.",
    "chatbots @Zelretch_Chats",
).add(
    "id",
    "<reply to message (optional)>",
    "Show the numeric IDs of the current chat, the replied user, and the replied message. Useful for configuring LOGGER_ID or OWNER_ID.",
    "id",
).add(
    "invite",
    "<username/id> (multiple allowed)",
    "Invite one or more users to the current chat via an invite link. Separate multiple usernames or IDs with spaces.",
    "invite @ZelretchUser",
    "Useful when the chat's privacy settings prevent adding users directly.",
).info(
    "Group and channel management — edit profile, title, description, username, invite links, and inspect chat membership."
).done()

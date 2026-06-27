from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from zelretch.core import Config, db, zelretch
from zelretch.functions.admins import is_user_admin


def on_message(
    command: str | list[str],
    group: int = 0,
    chat_type: list[ChatType] = None,
    admin_only: bool = False,
    allow_master: bool = False,
):
    if allow_master:
        _filter = (
            filters.command(command, Config.HANDLERS)
            & (filters.me | Config.MASTER_USERS)
            & ~filters.forwarded
            & ~filters.via_bot
        )
    else:
        _filter = (
            filters.command(command, Config.HANDLERS)
            & filters.me
            & ~filters.forwarded
            & ~filters.via_bot
        )

    def decorator(func):
        async def wrapper(client: Client, message: Message):
            sender = getattr(message, "from_user", None)
            client_user = getattr(client, "me", None)

            # Channel posts, anonymous-admin messages, service messages, and
            # some callback/listen updates can arrive without a real from_user.
            # Userbot commands need a concrete Telegram user id for the
            # self/master permission check, so ignore those updates instead of
            # crashing the dispatcher.
            if sender is None or client_user is None:
                return

            if client_user.id != sender.id:
                if not await db.is_master(client_user.id, sender.id):
                    return

            if admin_only and not message.chat.type == ChatType.PRIVATE:
                if not await is_user_admin(message.chat, client.me.id):
                    return await zelretch.edit(message, "𝖨 𝖺𝗆 𝗇𝗈𝗍 𝖺𝗇 𝖺𝖽𝗆𝗂𝗇 𝗁𝖾𝗋𝖾!")

            if chat_type and message.chat.type not in chat_type:
                return await zelretch.edit(message, "𝖢𝖺𝗇'𝗍 𝗎𝗌𝖾 𝗍𝗁𝗂𝗌 𝖼𝗈𝗆𝗆𝖺𝗇𝖽 𝗁𝖾𝗋𝖾!")

            await func(client, message)
            message.continue_propagation()

        for user in zelretch.users:
            user.add_handler(MessageHandler(wrapper, _filter), group)

        return wrapper

    return decorator


def custom_handler(filters: filters.Filter, group: int = 0):
    def decorator(func):
        async def wrapper(client: Client, message: Message):
            await func(client, message)
            message.continue_propagation()

        for user in zelretch.users:
            user.add_handler(MessageHandler(wrapper, filters), group)

        return wrapper

    return decorator

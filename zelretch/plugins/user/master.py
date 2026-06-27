from pyrogram import Client
from pyrogram.types import Message

from . import Config, HelpMenu, db, zelretch, on_message


@on_message("master", allow_master=True)
async def masterUsers(client: Client, message: Message):
    hell = await zelretch.edit(message, "__Fetching users...__")

    users = await db.get_masters(client.me.id)
    if not users:
        return await zelretch.delete(hell, "__No masters found!__")

    text = f"**Total masters:** `{len(users)}`\n\n"
    for user in users:
        try:
            user = await client.get_users(user["user_id"])
            mention = user.mention
            userid = user.id
        except Exception:
            userid = user["user_id"]
            mention = "Unknown Peer"
        text += f"• {mention} (`{userid}`)\n"

    await hell.edit(text)


@on_message("addmaster", allow_master=False)
async def addmaster(client: Client, message: Message):
    if len(message.command) < 2:
        if not message.reply_to_message:
            return await zelretch.delete(
                message,
                "__Reply to a user or give me a user id to add them as a master!__",
            )
        user = message.reply_to_message.from_user
    else:
        try:
            user = await client.get_users(message.command[1])
        except Exception:
            return await zelretch.delete(
                message, "__Give me a valid user id to add them as a master!__"
            )

    if user.id == client.me.id:
        return await zelretch.delete(message, "__I can't be a master of myself!__")

    if await db.is_master(client.me.id, user.id):
        return await zelretch.delete(message, "__This user is already a master!__")

    await db.add_master(client.me.id, user.id)
    await zelretch.delete(message, f"__Added {user.mention} as a master!__")

    Config.AUTH_USERS.add(user.id)
    Config.MASTER_USERS.add(user.id)


@on_message("delmaster", allow_master=False)
async def delmaster(client: Client, message: Message):
    if len(message.command) < 2:
        if not message.reply_to_message:
            return await zelretch.delete(
                message,
                "__Reply to a user or give me a user id to remove them from masters!__",
            )
        user = message.from_user
    else:
        try:
            user = await client.get_users(message.command[1])
        except Exception:
            return await zelretch.delete(
                message, "__Give me a valid user id to remove them from masters!__"
            )

    if await db.is_master(client.me.id, user.id):
        await db.rm_master(client.me.id, user.id)
        await zelretch.delete(message, f"__Removed {user.mention} from masters!__")

        Config.AUTH_USERS.remove(user.id)
        Config.MASTER_USERS.remove(user.id)
    else:
        await zelretch.delete(message, "__This user is not a master!__")


HelpMenu("master").add(
    "master",
    None,
    "Get a list of masters for your client.",
    "master",
    "A master can access some of the commands of your client.",
).add(
    "addmaster",
    "<reply/username/userid>",
    "Add a master in your client.",
    "addmaster",
    "Be careful while adding a master.",
).add(
    "delmaster",
    "<reply/username/userid>",
    "Remove a master from your client.",
    "delmaster",
).info(
    "Bound Masters"
).done()

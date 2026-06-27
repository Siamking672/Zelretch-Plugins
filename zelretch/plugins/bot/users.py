from kurigram import Client, filters
from kurigram.types import Message

from . import BotHelp, Config, Symbols, zelretch


@zelretch.bot.on_message(
    filters.command("addauth") & Config.AUTH_USERS
)
async def addauth(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await message.reply_text(
                "Reply to a user or give a user ID/username to register them as authorized magi."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception:
            return await message.reply_text(
                "Give a valid user ID/username to register as authorized magi."
            )
    else:
        user = message.reply_to_message.from_user

    if user.is_self:
        return await message.reply_text("I cannot register myself as authorized magi.")

    if user.id in Config.AUTH_USERS:
        return await message.reply_text(f"**{user.mention} is already authorized as a magus**")

    Config.AUTH_USERS.add(user.id)
    await message.reply_text(f"**Added {user.mention} to authorized magi!**")


@zelretch.bot.on_message(
    filters.command("delauth") & Config.AUTH_USERS
)
async def delauth(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await message.reply_text(
                "Reply to a user or give a user ID/username to register them as authorized magi."
            )
        try:
            user = await client.get_users(message.command[1])
        except Exception:
            return await message.reply_text(
                "Give a valid user ID/username to register as authorized magi."
            )
    else:
        user = message.reply_to_message.from_user

    if user.id in Config.AUTH_USERS:
        Config.AUTH_USERS.remove(user.id)
        await message.reply_text(f"**Removed {user.mention} from authorized magi!**")
    else:
        await message.reply_text(f"**{user.mention} is not registered as authorized magi**")


@zelretch.bot.on_message(
    filters.command("authlist") & Config.AUTH_USERS
)
async def authlist(client: Client, message: Message):
    text = "**🔴 Authorized Magi:**\n\n"
    for i, userid in enumerate(Config.AUTH_USERS):
        try:
            user = await client.get_users(userid)
            text += f"    {Symbols.anchor} {user.mention} (`{user.id}`)\n"
        except:
            text += f"    {Symbols.anchor} Auth User #{i+1} (`{userid}`)\n"

    await message.reply_text(text)


BotHelp("Magi").add(
    "addauth",
    "Register a user as authorized magi. Authorized magi can manage userbot contracts.",
).add("delauth", "Remove a user from authorized magi.").add(
    "authlist", "List all authorized magi."
).info(
    "Magi Registry"
).done()

import re

from kurigram import Client
from kurigram.types import Message

from . import HelpMenu, Symbols, handler, zelretch, on_message


@on_message("newfed", allow_master=True)
async def newfed(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, f"Usage: {handler}newfed <fedname>")

    bot_un = "@MissRose_bot"
    await client.unblock_user(bot_un)

    fedname = await zelretch.input(message)
    kaleido = await zelretch.edit(message, f"__Creating new federation__ **{fedname}**")

    extract_fedid = (
        lambda text: re.search(r"FedID: (\S+)", text).group(1)
        if re.search(r"FedID: (\S+)", text)
        else None
    )

    try:
        msg1 = await client.ask(bot_un, f"/newfed {fedname}", timeout=60)
    except Exception as e:
        return await zelretch.error(kaleido, f"`{e}`")

    if "created new federation" in msg1.text.lower():
        await kaleido.edit(
            f"**𝖭𝖾𝗐 𝖥𝖾𝖽𝖾𝗋𝖺𝗍𝗂𝗈𝗇 𝖼𝗋𝖾𝖺𝗍𝖾𝖽 𝗈𝗇 {bot_un}:** `{fedname}` \n**𝖥𝖾𝖽𝖨𝖽:** `{extract_fedid(msg1.text)[:-1]}`"
        )
    else:
        await zelretch.delete(kaleido, f"**Failed to create federation!**\n\n`{msg1.text}`")

    try:
        await msg1.request.delete()
        await msg1.delete()
    except:
        pass


@on_message("renamefed", allow_master=True)
async def renamefed(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, f"Usage: {handler}renamefed <new fedname>")

    bot_un = "@MissRose_bot"
    await client.unblock_user(bot_un)

    fedname = await zelretch.input(message)
    kaleido = await zelretch.edit(message, f"__Renaming federation to__ **{fedname}**")

    try:
        msg1 = await client.ask(bot_un, f"/renamefed {fedname}", timeout=60)
    except Exception as e:
        return await zelretch.error(kaleido, f"`{e}`")

    if "renamed your federation from" in msg1.text.lower():
        await kaleido.edit(f"**𝖥𝖾𝖽𝖾𝗋𝖺𝗍𝗂𝗈𝗇 𝗋𝖾𝗇𝖺𝗆𝖾𝖽 𝗍𝗈** `{fedname}`")
    else:
        await zelretch.delete(kaleido, f"**Failed to rename federation!**\n\n`{msg1.text}`")

    try:
        await msg1.request.delete()
        await msg1.delete()
    except:
        pass


@on_message("fedinfo", allow_master=True)
async def fedinfo(client: Client, message: Message):
    if len(message.command) < 2:
        fedid = ""
    else:
        fedid = message.command[1]

    bot_un = "@MissRose_bot"
    await client.unblock_user(bot_un)

    get_value = lambda pattern: pattern.group(1) if pattern else None
    kaleido = await zelretch.edit(message, "__Fetching federation info__")

    try:
        msg1 = await client.ask(bot_un, f"/fedinfo {fedid}", timeout=60)
    except Exception as e:
        return await zelretch.error(kaleido, f"`{e}`")

    if "fed info" in msg1.text.lower():
        fedid, name, creator, admins, bans, connected_chats, subscribed_feds = map(
            get_value,
            (
                re.search(r"FedID: (\S+)", msg1.text),
                re.search(r"Name: (.+)", msg1.text),
                re.search(r"Creator: (.+)", msg1.text),
                re.search(r"admins: (\d+)", msg1.text),
                re.search(r"bans: (\d+)", msg1.text),
                re.search(r"connected chats: (\d+)", msg1.text),
                re.search(r"subscribed feds: (\d+)", msg1.text),
            ),
        )

        await kaleido.edit(
            f"**{Symbols.anchor} 𝖥𝖾𝖽𝖨𝖽:** `{fedid}`\n"
            f"**{Symbols.anchor} 𝖭𝖺𝗆𝖾:** `{name}`\n"
            f"**{Symbols.anchor} 𝖢𝗋𝖾𝖺𝗍𝗈𝗋:** {creator}\n"
            f"**{Symbols.anchor} 𝖳𝗈𝗍𝖺𝗅 𝖺𝖽𝗆𝗂𝗇𝗌:** `{admins}`\n"
            f"**{Symbols.anchor} 𝖳𝗈𝗍𝖺𝗅 𝖻𝖺𝗇𝗌::** `{bans}`\n"
            f"**{Symbols.anchor} 𝖢𝗈𝗇𝗇𝖾𝖼𝗍𝖾𝖽 𝖢𝗁𝖺𝗍𝗌:** `{connected_chats}`\n"
            f"**{Symbols.anchor} 𝖲𝗎𝖻𝗌𝖼𝗋𝗂𝖻𝖾𝖽 𝖥𝖾𝖽𝖲:** `{subscribed_feds}`\n"
        )
    else:
        await zelretch.delete(kaleido, f"**Failed to fetch federation info!**\n\n`{msg1.text}`")

    try:
        await msg1.request.delete()
        await msg1.delete()
    except:
        pass


HelpMenu("federation").add(
    "newfed",
    "<name>",
    "Create a new federation on MissRose Bot. Federations let you ban a user across multiple chats at once via Rose.",
    "newfed Workshop Alliance",
).add(
    "renamefed",
    "<name>",
    "Rename an existing federation you own on MissRose Bot.",
    "renamefed Workshop Alliance v2",
).add(
    "fedinfo",
    "<fed id (optional)>",
    "Show information about a federation on MissRose Bot. Omit the ID to view your own federation.",
    "fedinfo fed-id",
).info(
    "Manage MissRose Bot federations — cross-chat ban networks controlled via the userbot."
).done()

from kurigram import Client
from kurigram.enums import ParseMode
from kurigram.types import Message

from zelretch.functions.utility import Gcast

from . import HelpMenu, handler, zelretch, on_message

gcast = Gcast()


@on_message("gcast", allow_master=True)
async def broadcast(client: Client, message: Message):
    if len(message.command) < 2 or not message.reply_to_message:
        return await zelretch.delete(
            message,
            f"Reply to a message with `{handler}gcast (all/groups/users) (copy)`",
        )

    mode = message.command[1].lower()
    if mode not in ["all", "groups", "users"]:
        return await zelretch.delete(
            message,
            f"Reply to a message with `{handler}gcast (all/groups/users) (copy)`",
        )

    tag = True
    if len(message.command) > 2:
        is_copy = message.command[2].lower()
        tag = False if is_copy == "copy" else True

    kaleido = await zelretch.edit(message, "Processing...")
    msg = await gcast.start(
        message.reply_to_message, client, message.command[1].strip(), tag
    )

    if msg:
        await kaleido.edit(
            msg[1], parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
        await zelretch.check_and_log("gcast", msg[1], msg[0])
    else:
        await kaleido.edit("No user or group found!")


HelpMenu("gcast").add(
    "gcast",
    "<target> <copy (optional)>",
    "Broadcast the replied message to every chat of the chosen type. By default the message is forwarded with a forward tag; pass 'copy' to send it as a fresh message instead.",
    "gcast groups copy",
    "Target must be one of: 'all' (every chat), 'groups' (supergroups only), or 'users' (private chats only). A log of failed deliveries is generated as a text file.",
).info(
    "Global broadcast — send one message to every group, user, or chat the userbot is in."
).done()

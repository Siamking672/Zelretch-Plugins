import uuid

from kurigram import Client
from kurigram.raw import base
from kurigram.raw.functions.channels import GetFullChannel
from kurigram.raw.functions.phone import (
    CreateGroupCall,
    DiscardGroupCall,
    ExportGroupCallInvite,
    GetGroupParticipants,
)
from kurigram.types import Message

from . import HelpMenu, Symbols, group_only, zelretch, on_message


@on_message("startvc", chat_type=group_only, admin_only=True, allow_master=True)
async def startvc(client: Client, message: Message):
    if len(message.command) > 1:
        call_name = await zelretch.input(message)
    else:
        call_name = "Zelretch VC"

    kaleido = await zelretch.edit(message, "Starting Voice Chat...")
    try:
        await client.invoke(
            CreateGroupCall(
                peer=(await client.resolve_peer(message.chat.id)),
                random_id=int(str(uuid.uuid4().int)[:8]),
                title=call_name,
            )
        )
        await zelretch.delete(kaleido, "Voice Chat started!")
    except Exception as e:
        await zelretch.error(kaleido, str(e))


@on_message("endvc", chat_type=group_only, admin_only=True, allow_master=True)
async def endvc(client: Client, message: Message):
    kaleido = await zelretch.edit(message, "Ending Voice Chat...")

    try:
        full_chat: base.messages.ChatFull = await client.invoke(
            GetFullChannel(channel=(await client.resolve_peer(message.chat.id)))
        )
        await client.invoke(DiscardGroupCall(call=full_chat.full_chat.call))
        await zelretch.delete(kaleido, "Voice Chat ended!")
    except Exception as e:
        await zelretch.error(kaleido, str(e))


@on_message("vclink", chat_type=group_only, allow_master=True)
async def vclink(client: Client, message: Message):
    kaleido = await zelretch.edit(message, "Getting Voice Chat link...")

    try:
        full_chat: base.messages.ChatFull = await client.invoke(
            GetFullChannel(channel=(await client.resolve_peer(message.chat.id)))
        )

        invite: base.phone.ExportedGroupCallInvite = await client.invoke(
            ExportGroupCallInvite(call=full_chat.full_chat.call)
        )
        await zelretch.delete(kaleido, f"Voice Chat Link: {invite.link}")
    except Exception as e:
        await zelretch.error(kaleido, f"`{e}`")


@on_message("vcmembers", chat_type=group_only, admin_only=True, allow_master=True)
async def vcmembers(client: Client, message: Message):
    kaleido = await zelretch.edit(message, "Getting Voice Chat members...")

    try:
        full_chat: base.messages.ChatFull = await client.invoke(
            GetFullChannel(channel=(await client.resolve_peer(message.chat.id)))
        )
        participants: base.phone.GroupParticipants = await client.invoke(
            GetGroupParticipants(
                call=full_chat.full_chat.call,
                ids=[],
                sources=[],
                offset="",
                limit=1000,
            )
        )
        count = participants.count
        text = f"**Total Voice Chat Members:** `{count}`\n\n"
        for participant in participants.participants:
            text += f"{Symbols.bullet} `{participant.peer.user_id}`\n"

        await kaleido.edit(text)
    except Exception as e:
        await zelretch.error(kaleido, str(e))


HelpMenu("voicechat").add(
    "startvc",
    "<voice chat name (optional)>",
    "Start a new voice chat in the current group. A custom title can be assigned; otherwise a default name is used.",
    "startvc Workshop VC",
    "Only admins with the manage voice chats permission can use this command.",
).add(
    "endvc",
    None,
    "End the active voice chat in the current group. All participants are disconnected.",
    "endvc",
    "Only admins with the manage voice chats permission can use this command.",
).add(
    "vclink",
    None,
    "Generate and share an invite link for the current group's active voice chat so external users can join.",
    "vclink",
).add(
    "vcmembers",
    None,
    "List every participant currently in the group's voice chat, including their user IDs.",
    "vcmembers",
    "Only admins with the manage voice chats permission can use this command.",
).info(
    "Voice chat management — start, end, share links to, and inspect members of group voice chats."
).done()

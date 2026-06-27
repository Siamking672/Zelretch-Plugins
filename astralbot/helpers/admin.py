"""Admin permission helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogram import Client
    from pyrogram.types import Chat


async def is_user_admin(client: "Client", chat_id: int | str, user_id: int) -> bool:
    """Check if a user is an admin in the given chat. Returns True for the
    chat's own creator / owner."""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        # member.status can be "owner", "administrator", "member", "restricted", "left", "banned"
        return member.status.value in ("owner", "administrator") if hasattr(member.status, "value") else str(member.status) in ("owner", "administrator")
    except Exception:
        return False


async def get_chat_admins(client: "Client", chat_id: int | str) -> list[int]:
    """Return a list of admin user IDs in the chat."""
    admins: list[int] = []
    try:
        async for m in client.get_chat_members(chat_id, filter="administrators"):
            if m.user:
                admins.append(m.user.id)
    except Exception:
        pass
    return admins


async def can_delete_messages(client: "Client", chat_id: int | str) -> bool:
    """Check if the bot account can delete messages in this chat."""
    try:
        me = await client.get_chat_member(chat_id, "me")
        return me.can_delete_messages if hasattr(me, "can_delete_messages") else False
    except Exception:
        return False


async def can_restrict_members(client: "Client", chat_id: int | str) -> bool:
    try:
        me = await client.get_chat_member(chat_id, "me")
        return me.can_restrict_members if hasattr(me, "can_restrict_members") else False
    except Exception:
        return False

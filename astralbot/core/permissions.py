"""
Permission helpers.

Tiered model (combined from both source projects):
    OWNER  — single owner (from env or auto-detected from primary session)
    SUDO   — env SUDO_USERS + DB masters (set via .addmaster)
    DEV    — env DEV_USERS (for trusted contributors)

The ``@on_command`` decorator takes ``allow_sudo=True`` to widen a command
from owner-only to sudo-allowed. Devs bypass everything except destructive
owner-only commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from astralbot.core.config import Config


class PermissionDenied(Exception):
    """Raised when a user lacks permission for a command."""


def can_run(command_perm: str, user_id: int, config: "Config", is_master: bool = False) -> bool:
    """Check if a user can run a command with the given permission tier.

    Args:
        command_perm: One of "owner", "sudo", "dev", "public".
                      "dev" allows owner+sudo+dev. "public" allows everyone.
        user_id: Telegram user ID of the caller.
        config: Config singleton.
        is_master: True if user is a DB master (looked up at call site).
    """
    if command_perm == "public":
        return True
    if config.is_owner(user_id):
        return True
    if command_perm == "dev":
        return config.is_dev(user_id) or config.is_sudo(user_id) or is_master
    if command_perm == "sudo":
        return config.is_sudo(user_id) or is_master or config.is_dev(user_id)
    if command_perm == "owner":
        return config.is_owner(user_id)
    return False

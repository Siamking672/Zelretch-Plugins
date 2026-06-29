# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Zelretch Addons - community plugin repository.

This folder is loaded automatically by the Zelretch main project when the
``ADDONS`` config flag is True (which is the default). Each ``.py`` file in
this folder is a plugin; subdirectories (such as ``inline/``) are walked
recursively.

Plugins here use the same ``zelretch_cmd`` decorator as core plugins - the
loader detects whether the calling file is under ``addons/`` and tags the
plugin as an addon rather than a core plugin.
"""

from __future__ import annotations

# Re-export everything from pyZelretch so addons can ``from plugins import *``
# the same way core plugins do.
from pyZelretch import (  # noqa: F401
    HNDLR,
    LOGS,
    asst,
    eod,
    eor,
    get_string,
    udB,
    zelretch_bot,
    zelretch_cmd,
    ultroid_cmd,
)

try:
    from kurigram.types import InlineKeyboardButton as Button  # type: ignore  # noqa: F401
except ImportError:  # pragma: no cover
    class Button:  # type: ignore[no-redef]
        def __init__(self, *a, **k):
            pass

bot = zelretch_bot

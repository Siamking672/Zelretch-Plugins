# Zelretch Addons — Kurigram-compatible plugins
# Copyright (C) 2021-2026 TeamUltroid (original UltroidAddons contributors)
# Copyright (C) 2026 Zelretch Contributors
#
# This is a separate plugin repository. It is loaded by the Zelretch main
# project via the plugin loader — see the main project's README for details.
#
# The `from . import *` line below exposes the same symbols that the original
# Ultroid addons expected (zelretch_bot, asst, udB, zelretch_cmd, eor, eod,
# get_string, HNDLR, etc.) so ported plugins keep working.

from plugins import *  # noqa: F401,F403
from zelretch import zelretch_bot as bot  # backwards-compatible alias

__all__ = ["bot"]

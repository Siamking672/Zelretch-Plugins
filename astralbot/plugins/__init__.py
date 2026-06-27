"""astralbot.plugins — decorator + help registry live here.

Plugins (built-in or user-installed) do NOT need to import from this package
explicitly; they use ``from astralbot import on_command, help_menu`` which
proxies through here.
"""

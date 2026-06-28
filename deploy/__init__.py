"""Zelretch one-command deployment wizard.

A self-contained Flask application that guides the user through bot
configuration via a local web page, then runs the actual deployment
(validate inputs -> connect MongoDB -> save config -> install deps ->
download plugins -> start bot).

Public entry point: :func:`deploy.server.create_app`.
"""

__version__ = "1.0.0"

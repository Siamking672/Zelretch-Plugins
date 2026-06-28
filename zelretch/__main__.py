import asyncio

from kurigram import idle

from zelretch import __version__
from zelretch.core import (
    Config,
    TemplateSetup,
    UserSetup,
    db,
    zelretch,
)
from zelretch.functions.runtime import initialize_git
from zelretch.functions.utility import BList, Flood, TGraph


async def main():
    await zelretch.startup()
    await db.connect()
    await UserSetup()
    await TemplateSetup()
    await Flood.updateFromDB()
    await BList.updateBlacklists()
    await TGraph.setup()
    await initialize_git(Config.PLUGINS_REPO)
    await zelretch.start_message(__version__)
    await idle()


if __name__ == "__main__":
    # Kurigram/Pyrogram clients and pyroaddon listeners bind futures to the
    # event loop that exists when the Client instances are created. Using
    # asyncio.run() creates a second loop, which breaks interactive flows such
    # as bot.ask() with: "future belongs to a different loop". Reuse the
    # bot client's loop instead.
    loop = getattr(zelretch.bot, "loop", None) or asyncio.get_event_loop()
    loop.run_until_complete(main())

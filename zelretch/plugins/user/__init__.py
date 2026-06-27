from kurigram.enums import ChatType

from zelretch.core.clients import zelretch
from zelretch.core.config import Config, Symbols
from zelretch.core.database import db
from zelretch.plugins.decorator import custom_handler, on_message
from zelretch.plugins.help import HelpMenu

handler = Config.HANDLERS[0]
bot = zelretch.bot

bot_only = [ChatType.BOT]
group_n_channel = [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]
group_only = [ChatType.GROUP, ChatType.SUPERGROUP]
private_n_bot = [ChatType.PRIVATE, ChatType.BOT]
private_only = [ChatType.PRIVATE]

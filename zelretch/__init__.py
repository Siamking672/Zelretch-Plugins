import os
import time
from platform import python_version

from pyrogram import __version__ as kurigram_version

from .core import LOGS, Config

START_TIME = time.time()


__version__ = {
    "zelretch": "3.0",
    "kurigram": kurigram_version,
    "python": python_version(),
}


def _validate_required_config() -> None:
    required = {
        "API_HASH": Config.API_HASH,
        "API_ID": Config.API_ID,
        "BOT_TOKEN": Config.BOT_TOKEN,
        "DATABASE_URL": Config.DATABASE_URL,
        "LOGGER_ID": Config.LOGGER_ID,
        "OWNER_ID": Config.OWNER_ID,
    }
    for key, value in required.items():
        if value in (None, 0, ""):
            LOGS.error(f"Please set your {key} !")
            raise SystemExit(1)


_validate_required_config()

for directory in (Config.DWL_DIR, Config.TEMP_DIR):
    if not os.path.isdir(directory):
        os.makedirs(directory)

import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    format="[%(asctime)s]:[%(name)s]:[%(levelname)s] - %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    handlers=[
        RotatingFileHandler(
            "Zelretch.log", maxBytes=(1024 * 1024 * 5), backupCount=10, encoding="utf-8"
        ),
        logging.StreamHandler(),
    ],
)


# Kurigram 2.x registers its internal logger under the name "pyrogram"
# (the package it ships as). Suppress its noisy INFO logs here.
logging.getLogger("pyrogram").setLevel(logging.ERROR)

LOGS = logging.getLogger("Zelretch")

# K: Keyboard Buttons

from pyrogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup


def gen_keyboard(collection: list, row: int = 2) -> list[list[KeyboardButton]]:
    keyboard = []
    for i in range(0, len(collection), row):
        kyb = []
        for x in collection[i : i + row]:
            kyb.append(KeyboardButton(x))
        keyboard.append(kyb)
    return keyboard




def session_inline_keyboard() -> list[list[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton("Summon", "session:new"),
            InlineKeyboardButton("Sever", "session:delete"),
        ],
        [
            InlineKeyboardButton("Roster", "session:list"),
            InlineKeyboardButton("Workshop", "session:home"),
        ],
    ]


def session_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("Summon"),
                KeyboardButton("Sever"),
            ],
            [
                KeyboardButton("Roster"),
                KeyboardButton("Workshop"),
            ],
        ],
        resize_keyboard=True,
    )


def start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("Command Seals"),
                KeyboardButton("Magi"),
            ],
            [
                KeyboardButton("Root Archive"),
            ],
        ],
        resize_keyboard=True,
    )

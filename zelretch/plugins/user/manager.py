import os

import psutil
from pyrogram.types import Message

from zelretch.core.config import all_env, os_configs
from zelretch.functions.paste import spaceBin
from zelretch.functions.templates import usage_templates
from zelretch.functions.runtime import restart, update_dotenv

from . import Config, HelpMenu, Symbols, db, zelretch, on_message


@on_message("getvar", allow_master=True)
async def getvar(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give a varname to fetch value.")

    varname = message.command[1]
    if varname.upper() in os_configs:
        value = os.environ.get(varname.upper(), None)
    else:
        value = await db.get_env(varname.upper())

    if isinstance(value, str):
        await zelretch.edit(
            message,
            f"{Symbols.anchor} **Variable Name:** `{varname.upper()}`\n{Symbols.anchor} **Value:** `{value}`",
        )
    elif value is None:
        await zelretch.delete(message, f"**Variable {varname} does not exist.**")


@on_message(["getallvar", "getallvars"], allow_master=True)
async def getallvar(_, message: Message):
    text = "**Configured variable names:**\n\n"
    for env in all_env:
        text += f"   {Symbols.anchor} `{env}`\n"

    for config in os_configs:
        text += f"   {Symbols.anchor} `{config}`\n"

    await zelretch.edit(message, text)


@on_message("setvar", allow_master=True)
async def setvar(_, message: Message):
    if len(message.command) < 3:
        return await zelretch.delete(
            message, "**Give a variable name and value with the command.**"
        )

    input_str = (await zelretch.input(message)).split(" ", 1)
    varname = input_str[0]
    varvalue = input_str[1]

    if varname.upper() in os_configs:
        oldValue = os.environ.get(varname.upper(), "None")
        await update_dotenv(varname.upper(), varvalue)
        await zelretch.edit(
            message,
            f"**{Symbols.anchor} Variable:** `{varname.upper()}` \n\n"
            f"**{Symbols.anchor} Old Value:** `{oldValue}` \n\n"
            f"**{Symbols.anchor} New Value:** `{varvalue}`\n\n"
            "__Restarting to apply changes.__",
        )
        return await restart()

    oldValue = await db.get_env(varname.upper())
    await db.set_env(varname.upper(), varvalue)
    await zelretch.delete(
        message,
        f"**{Symbols.anchor} Variable:** `{varname.upper()}` \n\n"
        f"**{Symbols.anchor} Old Value:** `{oldValue}` \n\n"
        f"**{Symbols.anchor} New Value:** `{varvalue}`",
    )


@on_message("delvar", allow_master=True)
async def delvar(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "**Give a variable name with the command.**")

    varname = message.command[1]
    if varname.upper() in os_configs:
        return await zelretch.error(
            message, "You can't delete this variable for security reasons."
        )

    if await db.is_env(varname.upper()):
        await db.rm_env(varname.upper())
        await zelretch.delete(
            message, f"**Variable** `{varname.upper()}` **deleted successfully.**"
        )
        return

    await zelretch.delete(message, "**No such variable found in database.**")


@on_message("usage", allow_master=True)
async def server_usage(_, message: Message):
    usage_message = await zelretch.edit(message, "Fetching usage info...")

    try:
        disk = psutil.disk_usage("/")
        diskTotal = int(disk.total / (1024.0**3))
        diskUsed = int(disk.used / (1024.0**3))
        diskPercent = disk.percent
    except Exception:
        diskTotal = 0
        diskUsed = 0
        diskPercent = 0

    try:
        memory = psutil.virtual_memory()
        memoryTotal = int(memory.total / (1024.0**3))
        memoryUsed = int(memory.used / (1024.0**3))
        memoryPercent = memory.percent
    except Exception:
        memoryTotal = 0
        memoryUsed = 0
        memoryPercent = 0

    await usage_message.edit(
        await usage_templates(
            appName="Zelretch",
            appHours=0,
            appMinutes=0,
            appPercentage=0,
            hours=0,
            minutes=0,
            percentage=0,
            diskUsed=diskUsed,
            diskTotal=diskTotal,
            diskPercent=diskPercent,
            memoryUsed=memoryUsed,
            memoryTotal=memoryTotal,
            memoryPercent=memoryPercent,
        )
    )


@on_message("logs", allow_master=True)
async def getLogs(_, message: Message):
    limit = int(message.command[1]) if len(message.command) > 1 else 100

    try:
        if os.path.exists("Zelretch.log"):
            with open("Zelretch.log", "r") as file:
                logData = file.readlines()
                logData = "".join(logData[-limit:])

            with open("log.txt", "w") as file:
                file.write(logData)

            link = spaceBin(logData)
            await message.reply_document(
                "log.txt",
                caption=f"**Link to logs:** [click here]({link})",
                file_name="log.txt",
            )
            os.remove("log.txt")
    except Exception as e:
        await zelretch.error(message, str(e))


HelpMenu("manager").add(
    "getvar",
    "<varname>",
    "Get value of a variable from env or database.",
    "getvar handler",
).add(
    "getallvar",
    None,
    "Get the name of every env and database variable.",
).add(
    "setvar",
    "<varname> <value>",
    "Set value of a variable in env or database.",
    "setvar handler !",
).add(
    "delvar", "<varname>", "Delete a database variable.", "delvar handler"
).add(
    "usage",
    None,
    "Get disk and RAM usage of the bot server.",
    "usage",
).add(
    "logs",
    "<limit>",
    "Get last 'n' lines of the log file. Default limit is 100.",
    "logs 69",
).info(
    "Manage your bot configuration and server usage."
).done()

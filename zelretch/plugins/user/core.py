import importlib
import os
import sys
from pathlib import Path

from kurigram import Client
from kurigram.enums import MessagesFilter, ParseMode
from kurigram.types import Message

from zelretch.core import ENV, Config, Symbols

from . import HelpMenu, bot, db, handler, zelretch, on_message


@on_message("help", allow_master=True)
async def help(client: Client, message: Message):
    kaleido = await zelretch.edit(message, "**Charging mana...**")
    if len(message.command) == 1:
        try:
            result = await client.get_inline_bot_results(bot.me.username, "help_menu")
            await client.send_inline_bot_result(
                message.chat.id,
                result.query_id,
                result.results[0].id,
                True,
            )
            return await kaleido.delete()
        except Exception as e:
            await zelretch.error(kaleido, str(e), 20)
            return

    plugin = await zelretch.input(message)
    if plugin.lower() in Config.CMD_MENU:
        try:
            await zelretch.edit(
                kaleido, Config.CMD_MENU[plugin.lower()], ParseMode.MARKDOWN
            )
            return
        except Exception as e:
            await zelretch.error(kaleido, str(e), 20)
            return

    available_plugins = f"{Symbols.bullet} **𝖠𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 𝗉𝗅𝗎𝗀𝗂𝗇𝗌:**\n\n"
    for i in sorted(list(Config.CMD_MENU.keys())):
        available_plugins += f"`{i}`, "
    available_plugins = available_plugins[:-2]
    available_plugins += (
        f"\n\n𝖣𝗈 `{handler}help <plugin name>` 𝗍𝗈 𝗀𝖾𝗍 detailed archive notes for that Mystic Code."
    )
    await zelretch.edit(kaleido, available_plugins, ParseMode.MARKDOWN)


@on_message("repo", allow_master=True)
async def repo(_, message: Message):
    REPO_TEXT = (
        "__Main Archive:__ [GitHub](https://github.com/Siamking672/Zelretch)\n"
        "__Mystic Codes Archive:__ [GitHub](https://github.com/Siamking672/Zelretch-Plugins)"
    )
    await zelretch.edit(message, REPO_TEXT, no_link_preview=True)


@on_message("plinfo", allow_master=True)
async def plugin_info(_, message: Message):
    plugin = await zelretch.input(message)
    if plugin.lower() in Config.CMD_MENU:
        try:
            await zelretch.edit(
                message, Config.CMD_MENU[plugin.lower()], ParseMode.MARKDOWN
            )
            return
        except Exception as e:
            await zelretch.error(message, str(e), 20)
            return
    await zelretch.error(message, f"**Invalid Plugin Name:** `{plugin}`", 20)


@on_message("cmdinfo", allow_master=True)
async def command_info(_, message: Message):
    cmd = await zelretch.input(message)
    if cmd.lower() in Config.CMD_INFO:
        try:
            cmd_dict = Config.CMD_INFO[cmd.lower()]
            template = (
                f"**🍀 𝖯𝗅𝗎𝗀𝗂𝗇:** `{cmd_dict['plugin']}.py`\n\n"
                f"**{Symbols.anchor} 𝖢𝗈𝗆𝗆𝖺𝗇𝖽:** `{cmd_dict['command']}`\n"
                f"**{Symbols.anchor} 𝖣𝖾𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇:** __{cmd_dict['description']}__\n"
                f"**{Symbols.anchor} 𝖤𝗑𝖺𝗆𝗉𝗅𝖾:** `{cmd_dict['example']}`\n"
                f"**{Symbols.anchor} 𝖭𝗈𝗍𝖾:** __{cmd_dict['note']}__\n"
            )
            await zelretch.edit(message, template, ParseMode.MARKDOWN)
            return
        except Exception as e:
            await zelretch.error(message, str(e), 20)
            return
    await zelretch.error(message, f"**Invalid Command Name:** `{cmd}`", 20)


@on_message("send", allow_master=True)
async def send_plugin(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me a plugin name to send.")

    plugin = message.command[1].lower().replace(".py", "").strip()
    if plugin not in Config.CMD_MENU:
        return await zelretch.delete(message, f"**Invalid Plugin Name:** `{plugin}`")

    try:
        await client.send_document(
            message.chat.id,
            f"./zelretch/plugins/user/{plugin}.py",
            caption=f"**🍀 𝖯𝗅𝗎𝗀𝗂𝗇:** `{plugin}.py`",
        )
        await zelretch.delete(message, f"**Sent:** `{plugin}.py`")
    except Exception as e:
        await zelretch.error(message, str(e), 20)


@on_message("install", allow_master=True)
async def install_plugins(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await zelretch.delete(message, "Reply to a plugin to install it.")

    kaleido = await zelretch.edit(message, "**Installing...**")
    plugin_path = await message.reply_to_message.download("./zelretch/plugins/user/")

    if not plugin_path.endswith(".py"):
        os.remove(plugin_path)
        return await zelretch.error(kaleido, "**Invalid Plugin:** Not a python file.", 20)

    plugin = plugin_path.split("/")[-1].replace(".py", "").strip()
    if plugin in Config.CMD_MENU:
        os.remove(plugin_path)
        return await zelretch.error(
            kaleido, f"**Plugin Already Installed:** `{plugin}.py`", 20
        )

    if "(" in plugin:
        os.remove(plugin_path)
        return await zelretch.error(
            kaleido, f"**Plugin Already Installed:** `{plugin}.py`", 20
        )

    try:
        shortname = Path(plugin_path).stem.replace(".py", "")
        path = Path(f"zelretch/plugins/user/{shortname}.py")
        name = "zelretch.plugins.user." + shortname
        spec = importlib.util.spec_from_file_location(name, path)
        load = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(load)
        sys.modules["zelretch.plugins.user." + shortname] = load
        await zelretch.edit(kaleido, f"**Installed:** `{plugin}.py`")
    except Exception as e:
        await zelretch.error(kaleido, str(e), 20)
        os.remove(plugin_path)


@on_message("uninstall", allow_master=True)
async def uninstall_plugins(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me a plugin name to uninstall.")

    plugin = message.command[1].lower().replace(".py", "").strip()
    if plugin not in Config.CMD_MENU:
        return await zelretch.delete(message, f"**Invalid Plugin Name:** `{plugin}`")

    try:
        os.remove(f"./zelretch/plugins/user/{plugin}.py")
        for i in Config.HELP_DICT[plugin]["commands"]:
            cmd = i["command"]
            for i in zelretch.users:
                i.remove_handler(cmd)
            del Config.CMD_INFO[cmd]
        del Config.HELP_DICT[plugin]
        del Config.CMD_MENU[plugin]
        await zelretch.delete(message, f"**Uninstalled:** `{plugin}.py`")
    except Exception as e:
        await zelretch.error(message, str(e), 20)


@on_message("installall", allow_master=True)
async def installall(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(
            message, "Give me channel username to install plugins."
        )

    try:
        chat = await client.get_chat(message.command[1])
    except Exception as e:
        return await zelretch.delete(message, f"**Invalid Channel Username:** `{e}`")

    kaleido = await zelretch.edit(message, f"**Installing plugins from {chat.title}...**")
    finalStr = f"{Symbols.check_mark} **𝖯𝗅𝗎𝗀𝗂𝗇𝗌 𝖨𝗇𝗌𝗍𝖺𝗅𝗅𝖾𝖽: {chat.title}**\n\n"
    count = 0

    async for msg in client.search_messages(chat.id, filter=MessagesFilter.DOCUMENT):
        if msg.document.file_name.endswith(".py"):
            dwl_path = await msg.download("./zelretch/plugins/user/")
            plugin = dwl_path.split("/")[-1].replace(".py", "").strip()
            if plugin in Config.CMD_MENU:
                os.remove(dwl_path)
                finalStr += (
                    f"   {Symbols.anchor} `{plugin}.py` - **𝖠𝗅𝗋𝖾𝖺𝖽𝗒 𝖨𝗇𝗌𝗍𝖺𝗅𝗅𝖾𝖽!**\n"
                )
                continue
            if "(" in plugin:
                os.remove(dwl_path)
                finalStr += (
                    f"   {Symbols.anchor} `{plugin}.py` - **𝖠𝗅𝗋𝖾𝖺𝖽𝗒 𝖨𝗇𝗌𝗍𝖺𝗅𝗅𝖾𝖽!**\n"
                )
                continue
            try:
                shortname = Path(dwl_path).stem.replace(".py", "")
                path = Path(f"zelretch/plugins/user/{shortname}.py")
                name = "zelretch.plugins.user." + shortname
                spec = importlib.util.spec_from_file_location(name, path)
                load = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(load)
                sys.modules["zelretch.plugins.user." + shortname] = load
                count += 1
                finalStr += f"   {Symbols.anchor} `{plugin}.py` - **𝖨𝗇𝗌𝗍𝖺𝗅𝗅𝖾𝖽!**\n"
            except Exception as e:
                os.remove(dwl_path)
                finalStr += (
                    f"   {Symbols.anchor} `{plugin}.py` - **𝖤𝗋𝗋𝗈𝗋 𝖨𝗇𝗌𝗍𝖺𝗅𝗅𝗂𝗇𝗀!**\n"
                )
                continue

    finalStr += f"\n**🍀 𝖳𝗈𝗍𝖺𝗅 𝖯𝗅𝗎𝗀𝗂𝗇𝗌 𝖨𝗇𝗌𝗍𝖺𝗅𝗅𝖾𝖽:** `{count}`"
    await kaleido.edit(finalStr, ParseMode.MARKDOWN, disable_web_page_preview=True)


@on_message("unload", allow_master=True)
async def unload_plugins(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me a plugin name to unload.")

    plugin = message.command[1].lower().replace(".py", "").strip()
    if plugin not in Config.CMD_MENU:
        return await zelretch.delete(message, f"**Invalid Plugin Name:** `{plugin}`")

    unloaded = await db.get_env(ENV.unload_plugins) or ""
    unloaded = unloaded.split(" ")
    if plugin in unloaded:
        return await zelretch.delete(message, f"**Already Unloaded:** `{plugin}.py`")

    unloaded.append(plugin)
    await db.set_env(ENV.unload_plugins, " ".join(unloaded))
    await zelretch.delete(
        message, f"**Unloaded:** `{plugin}.py` \n\n__Restart the bot to see changes.__"
    )


@on_message("load", allow_master=True)
async def load_plugins(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Give me a plugin name to load.")

    plugin = message.command[1].lower().replace(".py", "").strip()
    unloaded = await db.get_env(ENV.unload_plugins) or ""
    unloaded = unloaded.split(" ")
    if plugin not in unloaded:
        return await zelretch.delete(message, f"**Already Loaded:** `{plugin}.py`")

    unloaded.remove(plugin)
    await db.set_env(ENV.unload_plugins, " ".join(unloaded))
    await zelretch.delete(
        message, f"**Loaded:** `{plugin}.py` \n\n__Restart the bot to see changes.__"
    )


HelpMenu("help").add(
    "help",
    "<plugin name (optional)>",
    "Open the inline help menu listing every loaded plugin. Pass a plugin name to jump straight to its commands.",
    "help alive",
).add(
    "repo",
    None,
    "Show the GitHub links to the main wrapper repository and the plugin archive.",
    "repo",
).add(
    "plinfo",
    "<plugin name>",
    "Display the full help card for a single plugin, including every command it provides.",
    "plinfo alive",
).add(
    "cmdinfo",
    "<command name>",
    "Display the description, parameters, example, and notes for a single command.",
    "cmdinfo alive",
).add(
    "send",
    "<plugin name>",
    "Send the plugin's Python source file into the chat so others can install it.",
    "send alive",
).add(
    "install",
    "<reply to a .py file>",
    "Install a plugin by replying to a Python file. The plugin is loaded immediately without a restart.",
    None,
    "Only install plugins from sources you trust. Malicious plugins can read your session string and take over your account. The Zelretch project is not responsible for any damage caused by third-party plugins.",
).add(
    "uninstall",
    "<plugin name>",
    "Remove a plugin and all of its commands from the bot until the next restart.",
    "uninstall alive",
    "The plugin file is deleted from disk, so it will not reload after a restart either.",
).add(
    "installall",
    "<channel username>",
    "Install every .py file posted in a Telegram channel as a plugin. Useful for bulk-loading a plugin repository channel.",
    "installall @plugins_for_zelretch",
    "Only install plugins from channels you trust. Malicious plugins can compromise your account.",
).add(
    "unload",
    "<plugin name>",
    "Disable a plugin so its commands no longer work, without deleting the file. The plugin stays unloaded across restarts.",
    "unload alive",
    "Use the 'load' command to re-enable an unloaded plugin.",
).add(
    "load",
    "<plugin name>",
    "Re-enable a plugin that was previously unloaded with the 'unload' command.",
    "load alive",
).info(
    "Help system and plugin lifecycle — browse, install, uninstall, load, and unload Mystic Codes."
).done()

from zelretch.core import LOGS
from zelretch.functions.runtime import restart, gen_changelogs, initialize_git

from . import Config, HelpMenu, zelretch, on_message


@on_message("restart", allow_master=True)
async def restart_bot(_, message):
    await zelretch.edit(message, "Restarting bot.")
    try:
        await restart()
    except Exception as e:
        LOGS.error(e)


@on_message("shutdown", allow_master=True)
async def shutdown_bot(_, message):
    await zelretch.edit(
        message,
        "**[ ⚠️ ]** __Zelretch has closed the workshop. Start the Docker container again to reopen the Kaleidoscope.__",
    )
    try:
        await restart(shutdown=True)
    except Exception as e:
        LOGS.error(e)


@on_message("cleanup", allow_master=True)
async def cleanup_bot(_, message):
    await zelretch.edit(message, "**♻️ Cleanup completed.**")
    await restart(clean_up=True)


@on_message("update", allow_master=True)
async def update_bot(_, message):
    current = await zelretch.edit(message, "**🔄 Checking for plugin updates...**")

    if len(message.command) < 2:
        status, repo, force = await initialize_git(Config.PLUGINS_REPO)
        if not status:
            return await zelretch.error(current, repo)

        active_branch = repo.active_branch.name
        upstream = repo.remote("upstream")
        upstream.fetch(active_branch)

        changelogs = await gen_changelogs(repo, f"HEAD..upstream/{active_branch}")
        if not changelogs and not force:
            repo.__del__()
            return await zelretch.delete(
                current, "__There are no plugin updates available right now.__"
            )

        if force:
            return await current.edit(
                f"Force-sync in progress. Try again after it completes.\n\n{changelogs}",
                disable_web_page_preview=True,
            )

        return await current.edit(
            f"**Plugin update available:**\n\n{changelogs}",
            disable_web_page_preview=True,
        )

    cmd = message.command[1].lower()
    if cmd == "plugins":
        await current.edit("**Updated plugin repo. Restarting.**")
        return await restart(update=True)

    return await zelretch.delete(current, f"**[ ⚠️ ]** __Invalid update argument:__ `{cmd}`")


HelpMenu("power").add(
    "restart", None, "Restart the bot.", "restart"
).add(
    "shutdown",
    None,
    "Shutdown the bot. Start the Docker container again to bring it back online.",
    "shutdown",
).add(
    "cleanup",
    None,
    "Delete downloaded files and temp files.",
    "cleanup",
).add(
    "update",
    None,
    "Check whether plugin updates are available.",
    "update",
).add(
    "update plugins",
    None,
    "Update plugins to the latest code and restart.",
    "update plugins",
).info(
    "Commands to manage the running bot."
).done()

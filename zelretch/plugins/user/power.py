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
    "restart",
    None,
    "Restart the bot process in-place. The wizard replaces the running Python process via execv so no duplicate instances are spawned.",
    "restart",
).add(
    "shutdown",
    None,
    "Stop the bot and exit the process. The bot will not restart automatically — start the Docker container or run the wizard again to bring it back online.",
    "shutdown",
).add(
    "cleanup",
    None,
    "Delete every file in the downloads and temp directories to reclaim disk space, then recreate the empty directories.",
    "cleanup",
).add(
    "update",
    None,
    "Check the upstream plugin repository for new commits since the last update and show the changelog.",
    "update",
).add(
    "update plugins",
    None,
    "Pull the latest plugin code from the configured GitHub repository, install any new dependencies, and restart the bot to apply the changes.",
    "update plugins",
).info(
    "Bot lifecycle controls — restart, shut down, clean up temp files, and update plugins from the upstream repository."
).done()

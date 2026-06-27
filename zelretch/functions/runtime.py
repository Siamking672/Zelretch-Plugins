import asyncio
import contextlib
import math
import os
import shlex
import shutil
import sys
import time

from pathlib import Path

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError
from kurigram.types import Message

from zelretch.core import Config, Symbols

from .formatter import humanbytes, readable_time


async def progress(
    current: int, total: int, message: Message, start: float, process: str
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        complete_time = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + complete_time
        progress_str = "**[{0}{1}] : {2}%\n**".format(
            "".join(["●" for i in range(math.floor(percentage / 10))]),
            "".join(["○" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2),
        )
        msg = (
            progress_str
            + "__{0}__ **𝗈𝖿** __{1}__\n**𝖲𝗉𝖾𝖾𝖽:** __{2}/s__\n**𝖤𝖳𝖠:** __{3}__".format(
                humanbytes(current),
                humanbytes(total),
                humanbytes(speed),
                readable_time(estimated_total_time / 1000),
            )
        )
        await message.edit_text(f"**{process} ...**\n\n{msg}")


async def get_files_from_directory(directory: str) -> list:
    all_files = []
    for path, _, files in os.walk(directory):
        for file in files:
            all_files.append(os.path.join(path, file))
    return all_files


async def runcmd(cmd: str) -> tuple[str, str, int, int]:
    args = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode("utf-8", "replace").strip(),
        stderr.decode("utf-8", "replace").strip(),
        process.returncode,
        process.pid,
    )


async def update_dotenv(key: str, value: str) -> None:
    with open(".env", "r") as file:
        data = file.readlines()

    for index, line in enumerate(data):
        if line.startswith(f"{key}="):
            data[index] = f"{key}={value}\n"
            break

    with open(".env", "w") as file:
        file.writelines(data)


async def _stop_client(client) -> None:
    """Stop a Kurigram/Pyrogram client without blocking the active handler."""
    if client is None:
        return
    try:
        is_connected = getattr(client, "is_connected", None)
        if is_connected is False:
            return
        await client.stop(block=False)
    except TypeError:
        await client.stop()
    except Exception:
        pass


async def _stop_all_clients() -> None:
    """Release Telegram SQLite session handles before replacing the process."""
    try:
        from zelretch.core import zelretch

        for client in list(getattr(zelretch, "users", [])):
            await _stop_client(client)
        await _stop_client(getattr(zelretch, "bot", None))
    except Exception:
        pass
    await asyncio.sleep(1)


async def restart(
    update: bool = False,
    clean_up: bool = False,
    shutdown: bool = False,
):
    try:
        shutil.rmtree(Config.DWL_DIR)
        shutil.rmtree(Config.TEMP_DIR)
    except BaseException:
        pass

    if clean_up:
        os.makedirs(Config.DWL_DIR, exist_ok=True)
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        return

    await _stop_all_clients()

    if shutdown:
        os._exit(0)

    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)

    if update:
        cmd = (
            "git pull && "
            "pip3 install --root-user-action=ignore -U -r requirements.txt && "
            "exec python3 -m zelretch"
        )
        os.execvp("bash", ["bash", "-lc", cmd])

    # Replace the current Python process instead of killing it and spawning a
    # second copy. This avoids duplicate Zelretch instances and prevents
    # Kurigram/Pyrogram SQLite session files from staying locked.
    os.execv(sys.executable, [sys.executable, "-m", "zelretch"])


async def gen_changelogs(repo: Repo, branch: str) -> str:
    changelogs = ""
    commits = list(repo.iter_commits(branch))[:5]
    for index, commit in enumerate(commits):
        changelogs += f"**{Symbols.triangle_right} {index + 1}.** `{commit.summary}`\n"

    return changelogs


async def initialize_git(git_repo: str, branch: str = None):
    force = False
    branch = branch or Config.PLUGINS_BRANCH
    try:
        repo = Repo()
    except NoSuchPathError as pathErr:
        return False, pathErr, force
    except GitCommandError as gitErr:
        return False, gitErr, force
    except InvalidGitRepositoryError:
        repo = Repo.init()
        origin = repo.create_remote("upstream", f"https://github.com/{git_repo}")
        origin.fetch()
        refs = {ref.remote_head: ref for ref in origin.refs}
        selected_branch = branch
        if selected_branch not in refs:
            if "main" in refs:
                selected_branch = "main"
            elif "master" in refs:
                selected_branch = "master"
            else:
                selected_branch = next(iter(refs))
        repo.create_head(selected_branch, refs[selected_branch])
        repo.heads[selected_branch].set_tracking_branch(refs[selected_branch])
        repo.heads[selected_branch].checkout(True)
        force = True
    with contextlib.suppress(BaseException):
        repo.create_remote("upstream", f"https://github.com/{git_repo}")

    return True, repo, force

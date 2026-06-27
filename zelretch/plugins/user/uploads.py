import os
import time

from kurigram import Client
from kurigram.types import Message

from zelretch.functions.formatter import readable_time
from zelretch.functions.runtime import progress

from . import HelpMenu, db, zelretch, on_message


@on_message("upload", allow_master=True)
async def uploadfiles(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Provide a valid file path.")

    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, f"**Uploading...** `{query}`")

    if not os.path.exists(query):
        return await zelretch.error(kaleido, f"**Error:** `{query}` **not found.**")

    try:
        ul_start = time.time()
        await message.reply_document(
            query,
            progress=progress,
            progress_args=(kaleido, ul_start, f"**Uploading...** `{query}`"),
        )
        ul_time = readable_time(int(time.time() - ul_start))
        await zelretch.delete(kaleido, f"**Uploaded** `{query}` **in** `{ul_time}`")
    except Exception as e:
        return await zelretch.error(kaleido, f"**Error:** `{e}`")


@on_message("uploaddir", allow_master=True)
async def uploadDir(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Provide a valid directory path.")

    query = await zelretch.input(message)
    kaleido = await zelretch.edit(message, f"**Uploading...** `{query}`")

    if not os.path.exists(query):
        return await zelretch.error(kaleido, f"**Error:** `{query}` **not found.**")

    files_list = []
    for root, dirs, files in os.walk(query):
        for file in files:
            files_list.append(os.path.join(root, file))
        for dir in dirs:
            files_list.append(os.path.join(root, dir))

    uploaded = 0
    await kaleido.edit(f"**Uploading...** `{len(files_list)} files...`")

    ul_start = time.time()
    for file in files_list:
        try:
            ul_start_file = time.time()
            await message.reply_document(
                file,
                caption=f"**📂 File:** `{os.path.basename(file)}`",
                progress=progress,
                progress_args=(kaleido, ul_start_file, f"**Uploading...** `{file}`"),
            )
            uploaded += 1
        except Exception:
            continue

    ul_time = readable_time(int(time.time() - ul_start))
    await kaleido.edit(
        f"**Uploaded** `{uploaded}/{len(files_list)}` **files in** `{ul_time}`"
    )


HelpMenu("uploads").add(
    "upload",
    "<server file path>",
    "Upload a single file from the server's filesystem into the current chat. Useful for fetching logs, downloaded media, or generated files.",
    "upload /app/.zelretch_plugins/requirements.txt",
    "Be cautious — only upload files you are comfortable sharing with the chat.",
).add(
    "uploaddir",
    "<server directory path>",
    "Upload every file inside the specified server directory into the current chat, one by one.",
    "uploaddir ./downloads/",
    "Be cautious — large directories will produce many messages and may hit Telegram's rate limits.",
).info(
    "Server file uploader — push files from the bot's filesystem directly into Telegram chats."
).done()

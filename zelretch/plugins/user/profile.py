import datetime
import os

import requests
from kurigram import Client
from kurigram.types import InputMediaPhoto, Message

from zelretch.functions.templates import github_user_templates

from . import Config, HelpMenu, zelretch, on_message


@on_message("getpfp", allow_master=True)
async def getpfp(client: Client, message: Message):
    kaleido = await zelretch.edit(message, "Processing...")
    limit = 1

    if message.reply_to_message:
        user = message.reply_to_message.from_user
        reply_to = message.reply_to_message.id

        if len(message.command) >= 2:
            if message.command[1].isdigit():
                limit = int(message.command[1])
            elif message.command[1] == "all":
                limit = 0

    elif len(message.command) >= 2:
        try:
            user = await client.get_users(message.command[1])
            reply_to = message.id

            if len(message.command) > 2:
                if message.command[2].isdigit():
                    limit = int(message.command[2])
                elif message.command[2] == "all":
                    limit = 0

        except Exception as e:
            return await zelretch.error(kaleido, f"`{str(e)}`")

    else:
        return await zelretch.delete(
            kaleido, f"Reply to a message or pass a username/id to get the profile pic."
        )

    if not user.photo:
        return await zelretch.error(kaleido, f"User {user.mention} has no profile pic.")

    if limit == 1:
        async for photo in client.get_chat_photos(user.id, 1):
            await client.send_photo(
                message.chat.id,
                photo.file_id,
                f"**Profile Pic of User** {user.mention}",
                reply_to_message_id=reply_to,
            )
    else:
        profile_pics = []
        async for photo in client.get_chat_photos(user.id, limit):
            profile_pics.append(InputMediaPhoto(photo.file_id))

        await client.send_media_group(
            message.chat.id,
            profile_pics,
            reply_to_message_id=reply_to,
        )

    await kaleido.delete()


@on_message("setpfp", allow_master=True)
async def setpfp(client: Client, message: Message):
    if not message.reply_to_message:
        return await zelretch.delete(message, "Reply to a photo to set as profile pic.")

    kaleido = await zelretch.edit(message, "Processing...")

    try:
        if message.reply_to_message.photo:
            dwl_path = await message.reply_to_message.download(Config.DWL_DIR)
            await client.set_profile_photo(photo=dwl_path)
        elif message.reply_to_message.video:
            dwl_path = await message.reply_to_message.download(Config.DWL_DIR)
            await client.set_profile_photo(video=dwl_path)
        else:
            return await zelretch.delete(
                kaleido, "Reply to a photo or video to set as profile pic."
            )
    except Exception as e:
        return await zelretch.error(kaleido, f"`{str(e)}`")

    await zelretch.delete(kaleido, "Profile pic updated successfully.")
    await zelretch.check_and_log(
        "setpfp",
        f"**User:** {message.from_user.mention} (`{message.from_user.id}`)",
        dwl_path,
    )

    os.remove(dwl_path)


@on_message("setbio", allow_master=True)
async def setbio(client: Client, message: Message):
    bio = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Processing...")

    try:
        await client.update_profile(bio=bio)
    except Exception as e:
        return await zelretch.error(kaleido, f"`{str(e)}`")

    await zelretch.delete(kaleido, "Bio updated successfully.")
    await zelretch.check_and_log(
        "setbio",
        f"**User:** {message.from_user.mention} (`{message.from_user.id}`)\n\n**Bio:** `{bio}`",
    )


@on_message("setname", allow_master=True)
async def setname(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Pass a name to set.")

    name = await zelretch.input(message)
    kaleido = await zelretch.edit(message, "Processing...")

    try:
        await client.update_profile(first_name=name)
    except Exception as e:
        return await zelretch.error(kaleido, f"`{str(e)}`")

    await zelretch.delete(kaleido, "Name updated successfully.")
    await zelretch.check_and_log(
        "setname",
        f"**User:** {message.from_user.mention} (`{message.from_user.id}`)\n\n**Name:** `{name}`",
    )


@on_message("setusername", allow_master=True)
async def setusername(client: Client, message: Message):
    username = message.command[1] if len(message.command) > 1 else None
    kaleido = await zelretch.edit(message, "Processing...")

    try:
        await client.set_username(username)
    except Exception as e:
        return await zelretch.error(kaleido, f"`{str(e)}`")

    await zelretch.delete(kaleido, "Username updated successfully.")
    await zelretch.check_and_log(
        "setusername",
        f"**User:** {message.from_user.mention} (`{message.from_user.id}`)\n\n**Username:** `{username}`",
    )


@on_message("delpfp", allow_master=True)
async def delpfp(client: Client, message: Message):
    limit = (
        1
        if len(message.command) < 2
        else int(message.command[1])
        if message.command[1].isdigit()
        else 1
    )

    kaleido = await zelretch.edit(message, "Processing...")
    profile_pics = []

    async for photo in client.get_chat_photos(client.me.id, limit):
        profile_pics.append(photo.file_id)

    if not profile_pics:
        return await zelretch.error(kaleido, "No profile pics found.")

    await client.delete_profile_photos(profile_pics)


@on_message("github", allow_master=True)
async def gituser(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.delete(message, "Pass a github username to search.")

    kaleido = await zelretch.edit(message, "Processing...")
    username = message.command[1]

    try:
        response = requests.get(f"https://api.github.com/users/{username}").json()
        avatar_url = response["avatar_url"]
        bio = response["bio"]
        blog = response["blog"]
        company = response["company"]
        created_at = datetime.datetime.strptime(
            response["created_at"], "%Y-%m-%dT%H:%M:%SZ"
        )
        email = response["email"]
        followers = response["followers"]
        following = response["following"]
        git_id = response["id"]
        id_type = response["type"]
        location = response["location"]
        name = response["name"]
        profile_url = response["html_url"]
        public_gists = response["public_gists"]
        public_repos = response["public_repos"]
        username = response["login"]
        if not bio:
            bio = "No bio found."

        file = f"{Config.TEMP_DIR}{username}.jpg"
        resp = requests.get(avatar_url)
        with open(file, "wb") as f:
            f.write(resp.content)

        await message.reply_photo(
            file,
            caption=await github_user_templates(
                username=username,
                git_id=git_id,
                id_type=id_type,
                name=name,
                profile_url=profile_url,
                blog=blog,
                company=company,
                email=email,
                location=location,
                public_repos=public_repos,
                public_gists=public_gists,
                followers=followers,
                following=following,
                created_at=created_at.strftime("%d %B %Y"),
                bio=bio,
            ),
        )
        await kaleido.delete()
        os.remove(file)
    except Exception as e:
        return await zelretch.error(kaleido, f"`{str(e)}`")


HelpMenu("profile").add(
    "getpfp",
    "<reply to user> or <username/id> <count>",
    "Fetch up to N of a user's most recent profile pictures and upload them into the chat.",
    "getpfp @ZelretchUser 5",
).add(
    "setpfp",
    "<reply to photo>",
    "Set the replied photo as the profile picture of the userbot's Telegram account.",
    "setpfp",
).add(
    "setbio",
    "<new bio text>",
    "Update the bio (about) text of the userbot's Telegram account.",
    "setbio Embracing the Kaleidoscope",
    "Omit the argument entirely to clear the bio.",
).add(
    "setname",
    "<new display name>",
    "Change the first name (display name) of the userbot's Telegram account.",
    "setname Zelretch",
).add(
    "setusername",
    "<new username>",
    "Set or change the public username of the userbot's Telegram account.",
    "setusername Zelretch",
    "Omit the argument entirely to remove the username.",
).add(
    "delpfp",
    "<count>",
    "Delete up to N of the userbot's most recent profile pictures.",
    "delpfp 5",
    "Pass 0 to delete every profile picture in one go.",
).add(
    "github",
    "<github username>",
    "Fetch the public GitHub profile of a user, showing avatar, bio, follower counts, and links to repositories.",
    "github hellboy-op",
).info(
    "Profile management — view and edit the userbot's profile picture, bio, name, username; fetch others' profile pictures; and look up GitHub users."
).done()

"""Zelretch message templates.

Every template in this module follows a clean, modern layout:

* Plain-ASCII labels (no mathematical Unicode) so messages are
  searchable, lightweight, and render consistently across devices.
* A single consistent bullet glyph (``▸``) for list items.
* Section headers in bold with a thin divider line underneath.
* Generous whitespace between sections.
* The Fate / Rin Tohsaka theme is carried by the ``◆`` (diamond) and
  ``▸`` (arrow) glyphs plus the ruby-red accent emoji where appropriate.

All templates are stored as the first element of a one-item list so the
``random.choice()`` calls in the render functions still work when users
add their own custom templates via ``setvar``.
"""

import random

from zelretch import __version__
from zelretch.core import ENV, db


# ---------------------------------------------------------------------------
# Core status templates
# ---------------------------------------------------------------------------

ALIVE_TEMPLATES = [
    (
        "◆ **Zelretch Workshop** ◆\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**Status:** `Active`\n"
        "**Master:** {owner}\n\n"
        "▸ **Kurigram:** `{kurigram}`\n"
        "▸ **Zelretch:** `{zelretch}`\n"
        "▸ **Python:** `{python}`\n"
        "▸ **Uptime:** `{uptime}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "_Rin Tohsaka Theme_"
    ),
]

PING_TEMPLATES = [
    (
        "◆ **Gandr**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "▸ **Response:** `{speed} ms`\n"
        "▸ **Uptime:** `{uptime}`\n"
        "▸ **Master:** {owner}"
    ),
]

HELP_MENU_TEMPLATES = [
    (
        "◆ **Grimoire** ◆\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**For:** {owner}\n\n"
        "▸ **Mystic Codes:** `{plugins}`\n"
        "▸ **Spells:** `{commands}`\n\n"
        "Page **{current}** of **{last}**"
    ),
]

COMMAND_MENU_TEMPLATES = [
    (
        "◆ **Mystic Code:** `{file}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "_{info}_\n\n"
        "▸ **Loaded Spells:** `{commands}`"
    ),
]


# ---------------------------------------------------------------------------
# Anime / Manga / Character (AniList)
# ---------------------------------------------------------------------------

ANIME_TEMPLATES = [
    (
        "◆ **{name}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "▸ **Score:** `{score}`\n"
        "▸ **Source:** `{source}`\n"
        "▸ **Type:** `{mtype}`\n"
        "▸ **Episodes:** `{episodes}`\n"
        "▸ **Duration:** `{duration} min`\n"
        "▸ **Status:** `{status}`\n"
        "▸ **Format:** `{format}`\n"
        "▸ **Genre:** `{genre}`\n"
        "▸ **Tags:** `{tags}`\n"
        "▸ **Adult Rated:** `{isAdult}`\n"
        "▸ **Studio:** `{studio}`\n\n"
        "▸ **Trailer:** {trailer}\n"
        "▸ **Website:** {siteurl}\n"
        "▸ **Synopsis:** [Read]({description})"
    ),
]

MANGA_TEMPLATES = [
    (
        "◆ **{name}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "▸ **Score:** `{score}`\n"
        "▸ **Source:** `{source}`\n"
        "▸ **Type:** `{mtype}`\n"
        "▸ **Chapters:** `{chapters}`\n"
        "▸ **Volumes:** `{volumes}`\n"
        "▸ **Status:** `{status}`\n"
        "▸ **Format:** `{format}`\n"
        "▸ **Genre:** `{genre}`\n"
        "▸ **Adult Rated:** `{isAdult}`\n\n"
        "▸ **Website:** {siteurl}\n"
        "▸ **Synopsis:** [Read]({description})"
    ),
]

CHARACTER_TEMPLATES = [
    (
        "◆ **{name}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "▸ **Gender:** `{gender}`\n"
        "▸ **Date of Birth:** `{date_of_birth}`\n"
        "▸ **Age:** `{age}`\n"
        "▸ **Blood Type:** `{blood_type}`\n"
        "▸ **Favorites:** `{favorites}`\n"
        "▸ **Website:** {siteurl}{role_in}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "{description}"
    ),
]

AIRING_TEMPLATES = [
    (
        "◆ **{name}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "▸ **Status:** `{status}`\n"
        "▸ **Episode:** `{episode}`\n\n"
        "{airing_info}"
    ),
]

ANILIST_USER_TEMPLATES = [
    (
        "◆ **{name}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**Anime**\n"
        "▸ **Count:** `{anime_count}`\n"
        "▸ **Mean Score:** `{anime_score}`\n"
        "▸ **Minutes Watched:** `{minutes}`\n"
        "▸ **Episodes:** `{episodes}`\n\n"
        "**Manga**\n"
        "▸ **Count:** `{manga_count}`\n"
        "▸ **Mean Score:** `{manga_score}`\n"
        "▸ **Chapters Read:** `{chapters}`\n"
        "▸ **Volumes Read:** `{volumes}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "▸ **Profile:** {siteurl}"
    ),
]


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

GITHUB_USER_TEMPLATES = [
    (
        "◆ **{username}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "▸ **Name:** [{name}]({profile_url})\n"
        "▸ **Type:** `{id_type}`\n"
        "▸ **ID:** `{git_id}`\n\n"
        "**Links**\n"
        "▸ **Blog:** {blog}\n"
        "▸ **Company:** {company}\n"
        "▸ **Email:** {email}\n"
        "▸ **Location:** {location}\n\n"
        "**Stats**\n"
        "▸ **Repositories:** `{public_repos}`\n"
        "▸ **Gists:** `{public_gists}`\n"
        "▸ **Followers:** `{followers}`\n"
        "▸ **Following:** `{following}`\n"
        "▸ **Created:** `{created_at}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "_{bio}_"
    ),
]


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

STATISTICS_TEMPLATES = [
    (
        "◆ **{name}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**Channels**\n"
        "▸ **Total:** `{channels}`\n"
        "▸ **Admin:** `{ch_admin}`\n"
        "▸ **Owner:** `{ch_owner}`\n\n"
        "**Groups**\n"
        "▸ **Total:** `{groups}`\n"
        "▸ **Admin:** `{gc_admin}`\n"
        "▸ **Owner:** `{gc_owner}`\n\n"
        "**Others**\n"
        "▸ **Private Chats:** `{users}`\n"
        "▸ **Bots:** `{bots}`\n"
        "▸ **Unread Messages:** `{unread_msg}`\n"
        "▸ **Unread Mentions:** `{unread_mention}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⏱ **Time Taken:** `{time_taken}`"
    ),
]


# ---------------------------------------------------------------------------
# Global admin actions
# ---------------------------------------------------------------------------

GBAN_TEMPLATES = [
    (
        "◆ **{gtype}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "▸ **Target:** {name}\n"
        "▸ **Success:** `{success}`\n"
        "▸ **Failed:** `{failed}`\n"
        "▸ **Reason:** {reason}"
    ),
]


# ---------------------------------------------------------------------------
# Server usage
# ---------------------------------------------------------------------------

USAGE_TEMPLATES = [
    (
        "◆ **Server Usage**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**Dyno — {appName}**\n"
        "▸ **Used:** `{appHours}h {appMinutes}m` (`{appPercentage}%`)\n\n"
        "**Dyno — This Month**\n"
        "▸ **Remaining:** `{hours}h {minutes}m` (`{percentage}%`)\n\n"
        "**Disk**\n"
        "▸ **Used:** `{diskUsed}GB` / `{diskTotal}GB` (`{diskPercent}%`)\n\n"
        "**Memory**\n"
        "▸ **Used:** `{memoryUsed}GB` / `{memoryTotal}GB` (`{memoryPercent}%`)"
    ),
]


# ---------------------------------------------------------------------------
# User / Chat info
# ---------------------------------------------------------------------------

USER_INFO_TEMPLATES = [
    (
        "◆ **User Info**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**{mention}**\n\n"
        "▸ **First Name:** `{firstName}`\n"
        "▸ **Last Name:** `{lastName}`\n"
        "▸ **User ID:** `{userId}`\n"
        "▸ **DC:** `{dcId}`\n\n"
        "**Details**\n"
        "▸ **Common Groups:** `{commonGroups}`\n"
        "▸ **Pictures:** `{totalPictures}`\n"
        "▸ **Restricted:** `{isRestricted}`\n"
        "▸ **Verified:** `{isVerified}`\n"
        "▸ **Bot:** `{isBot}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "_{bio}_"
    ),
]

CHAT_INFO_TEMPLATES = [
    (
        "◆ **Chat Info**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**{chatName}**\n\n"
        "▸ **Chat ID:** `{chatId}`\n"
        "▸ **Link:** {chatLink}\n"
        "▸ **Owner:** {chatOwner}\n"
        "▸ **DC:** `{dcId}`\n\n"
        "**Members**\n"
        "▸ **Total:** `{membersCount}`\n"
        "▸ **Admins:** `{adminsCount}`\n"
        "▸ **Bots:** `{botsCount}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "_{description}_"
    ),
]


# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------

async def alive_template(owner: str, uptime: str) -> str:
    template = await db.get_env(ENV.alive_template)
    if template:
        message = template
    else:
        message = random.choice(ALIVE_TEMPLATES)
    return message.format(
        owner=owner,
        kurigram=__version__["kurigram"],
        zelretch=__version__["zelretch"],
        python=__version__["python"],
        uptime=uptime,
    )


async def ping_template(speed: float, uptime: str, owner: str) -> str:
    template = await db.get_env(ENV.ping_template)
    if template:
        message = template
    else:
        message = random.choice(PING_TEMPLATES)
    return message.format(speed=speed, uptime=uptime, owner=owner)


async def help_template(
    owner: str, cmd_n_plgn: tuple[int, int], page: tuple[int, int]
) -> str:
    template = await db.get_env(ENV.help_template)
    if template:
        message = template
    else:
        message = random.choice(HELP_MENU_TEMPLATES)
    return message.format(
        owner=owner,
        commands=cmd_n_plgn[0],
        plugins=cmd_n_plgn[1],
        current=page[0],
        last=page[1],
    )


async def command_template(file: str, info: str, commands: str) -> str:
    template = await db.get_env(ENV.command_template)
    if template:
        message = template
    else:
        message = random.choice(COMMAND_MENU_TEMPLATES)
    return message.format(file=file, info=info, commands=commands)


async def anime_template(**kwargs) -> str:
    template = await db.get_env(ENV.anime_template)
    if template:
        message = template
    else:
        message = random.choice(ANIME_TEMPLATES)
    return message.format(**kwargs)


async def manga_templates(**kwargs) -> str:
    template = await db.get_env(ENV.manga_template)
    if template:
        message = template
    else:
        message = random.choice(MANGA_TEMPLATES)
    return message.format(**kwargs)


async def character_templates(**kwargs) -> str:
    template = await db.get_env(ENV.character_template)
    if template:
        message = template
    else:
        message = random.choice(CHARACTER_TEMPLATES)
    return message.format(**kwargs)


async def airing_templates(**kwargs) -> str:
    template = await db.get_env(ENV.airing_template)
    if template:
        message = template
    else:
        message = random.choice(AIRING_TEMPLATES)
    return message.format(**kwargs)


async def anilist_user_templates(
    name: str, anime: tuple, manga: tuple, siteurl: str
) -> str:
    template = await db.get_env(ENV.anilist_user_template)
    if template:
        message = template
    else:
        message = random.choice(ANILIST_USER_TEMPLATES)
    return message.format(
        name=name,
        anime_count=anime[0],
        anime_score=anime[1],
        minutes=anime[2],
        episodes=anime[3],
        manga_count=manga[0],
        manga_score=manga[1],
        chapters=manga[2],
        volumes=manga[3],
        siteurl=siteurl,
    )


async def statistics_templates(**kwargs) -> str:
    template = await db.get_env(ENV.statistics_template)
    if template:
        message = template
    else:
        message = random.choice(STATISTICS_TEMPLATES)
    return message.format(**kwargs)


async def github_user_templates(**kwargs) -> str:
    template = await db.get_env(ENV.github_user_template)
    if template:
        message = template
    else:
        message = random.choice(GITHUB_USER_TEMPLATES)
    return message.format(**kwargs)


async def gban_templates(**kwargs) -> str:
    template = await db.get_env(ENV.gban_template)
    if template:
        message = template
    else:
        message = random.choice(GBAN_TEMPLATES)
    return message.format(**kwargs)


async def usage_templates(**kwargs) -> str:
    template = await db.get_env(ENV.usage_template)
    if template:
        message = template
    else:
        message = random.choice(USAGE_TEMPLATES)
    return message.format(**kwargs)


async def user_info_templates(**kwargs) -> str:
    template = await db.get_env(ENV.user_info_template)
    if template:
        message = template
    else:
        message = random.choice(USER_INFO_TEMPLATES)
    return message.format(**kwargs)


async def chat_info_templates(**kwargs) -> str:
    template = await db.get_env(ENV.chat_info_template)
    if template:
        message = template
    else:
        message = random.choice(CHAT_INFO_TEMPLATES)
    return message.format(**kwargs)

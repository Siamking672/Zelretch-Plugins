import random

from zelretch import __version__
from zelretch.core import ENV, db

ALIVE_TEMPLATES = [
    (
        "🔴 **Zelretch Workshop: Active**\n\n"
        "╭────── Kaleidoscope Core ──────\n"
        "│ **Master:** {owner}\n"
        "│ **Kurigram:** `{kurigram}`\n"
        "│ **Zelretch:** `{zelretch}`\n"
        "│ **Python:** `{python}`\n"
        "│ **Uptime:** `{uptime}`\n"
        "╰────── Rin Tohsaka Theme ──────"
    ),
]

PING_TEMPLATES = [
    """**🔴 Gandr fired.**

♦ **Response:** `{speed} ms`
♦ **Uptime:** `{uptime}`
♦ **Master:** {owner}""",
]

HELP_MENU_TEMPLATES = [
    """**📕 Grimoire for:** {owner}

__Loaded__ **{plugins} Mystic Codes** __with__ **{commands} spells** __ready for deployment.__

**📑 Page:** __{current}/{last}__""",
]

COMMAND_MENU_TEMPLATES = [
    """**Mystic Code:** `{file}`
**Archive Note:** __{info} 🔴__

**📜 Loaded Spells:** `{commands}`""",
]

ANIME_TEMPLATES = [
    """
{name}

╭────────────────•
╰➢ **𝖲𝖼𝗈𝗋𝖾:** `{score}`
╰➢ **𝖲𝗈𝗎𝗋𝖼𝖾:** `{source}`
╰➢ **𝖳𝗒𝗉𝖾:** `{mtype}`
╰➢ **𝖤𝗉𝗂𝗌𝗈𝖽𝖾𝗌:** `{episodes}`
╰➢ **𝖣𝗎𝗋𝖺𝗍𝗂𝗈𝗇:** `{duration} minutes`
╰➢ **𝖲𝗍𝖺𝗍𝗎𝗌:** `{status}`
╰➢ **𝖥𝗈𝗋𝗆𝖺𝗍:** `{format}`
╰➢ **𝖦𝖾𝗇𝗋𝖾:** `{genre}`
╰➢ **𝖳𝖺𝗀𝗌:** `{tags}`
╰➢ **𝖠𝖽𝗎𝗅𝗍 𝖱𝖺𝗍𝖾𝖽:** `{isAdult}`
╰➢ **𝖲𝗍𝗎𝖽𝗂𝗈:** `{studio}`
╰➢ **𝖳𝗋𝖺𝗂𝗅𝖾𝗋:** {trailer}
╰➢ **𝖶𝖾𝖻𝗌𝗂𝗍𝖾:** {siteurl}
╰➢ **𝖲𝗒𝗇𝗈𝗉𝗌𝗂𝗌:** [𝖢𝗅𝗂𝖼𝗄 𝖧𝖾𝗋𝖾]({description})
╰────────────────•
"""
]

MANGA_TEMPLATES = [
    """
{name}

╭────────────────•
╰➢ **𝖲𝖼𝗈𝗋𝖾:** `{score}`
╰➢ **𝖲𝗈𝗎𝗋𝖼𝖾:** `{source}`
╰➢ **𝖳𝗒𝗉𝖾:** `{mtype}`
╰➢ **𝖢𝗁𝖺𝗉𝗍𝖾𝗋𝗌:** `{chapters}`
╰➢ **𝖵𝗈𝗅𝗎𝗆𝖾𝗌:** `{volumes}`
╰➢ **𝖲𝗍𝖺𝗍𝗎𝗌:** `{status}`
╰➢ **𝖥𝗈𝗋𝗆𝖺𝗍:** `{format}`
╰➢ **𝖦𝖾𝗇𝗋𝖾:** `{genre}`
╰➢ **𝖠𝖽𝗎𝗅𝗍 𝖱𝖺𝗍𝖾𝖽:** `{isAdult}`
╰➢ **𝖶𝖾𝖻𝗌𝗂𝗍𝖾:** {siteurl}
╰➢ **𝖲𝗒𝗇𝗈𝗉𝗌𝗂𝗌:** [𝖢𝗅𝗂𝖼𝗄 𝖧𝖾𝗋𝖾]({description})
╰────────────────•
"""
]

CHARACTER_TEMPLATES = [
    """
{name}

╭────────────────•
╰➢ **𝖦𝖾𝗇𝖽𝖾𝗋:** `{gender}`
╰➢ **𝖣𝖺𝗍𝖾 𝗈𝖿 𝖡𝗂𝗋𝗍𝗁:** `{date_of_birth}`
╰➢ **𝖠𝗀𝖾:** `{age}`
╰➢ **𝖡𝗅𝗈𝗈𝖽 𝖳𝗒𝗉𝖾:** `{blood_type}`
╰➢ **𝖥𝖺𝗏𝗈𝗎𝗋𝗂𝗍𝖾𝗌:** `{favorites}`
╰➢ **𝖶𝖾𝖻𝗌𝗂𝗍𝖾:** {siteurl}{role_in}
╰────────────────•
{description}
"""
]

AIRING_TEMPLATES = [
    """
{name}

╭────────────────•
╰➢ **𝖲𝗍𝖺𝗍𝗎𝗌:** `{status}`
╰➢ **𝖤𝗉𝗂𝗌𝗈𝖽𝖾:** `{episode}`
╰────────────────•{airing_info}
"""
]

ANILIST_USER_TEMPLATES = [
    """
**💫 {name}**

╭──── 𝖠𝗇𝗂𝗆𝖾 ─────•
╰➢ **𝖢𝗈𝗎𝗇𝗍:** `{anime_count}`
╰➢ **𝖲𝖼𝗈𝗋𝖾:** `{anime_score}`
╰➢ **𝖬𝗂𝗇𝗎𝗍𝖾𝗌 𝖲𝗉𝖾𝗇𝗍:** `{minutes}`
╰➢ **𝖤𝗉𝗂𝗌𝗈𝖽𝖾𝗌 𝖶𝖺𝗍𝖼𝗁𝖾𝖽:** `{episodes}`
╰────────────────•
╭──── 𝖬𝖺𝗇𝗀𝖺 ─────•
╰➢ **𝖢𝗈𝗎𝗇𝗍:** `{manga_count}`
╰➢ **𝖲𝖼𝗈𝗋𝖾:** `{manga_score}`
╰➢ **𝖢𝗁𝖺𝗉𝗍𝖾𝗋𝗌:** `{chapters}`
╰➢ **𝖵𝗈𝗅𝗎𝗆𝖾𝗌:** `{volumes}`
╰────────────────•

𝖶𝖾𝖻𝗌𝗂𝗍𝖾: {siteurl}
"""
]

CLIMATE_TEMPLATES = [
    """
🌆 {city_name}, {country}

╭────────────────•
╰➢ **𝖶𝖾𝖺𝗍𝗁𝖾𝗋:** {weather}
╰➢ **𝖳𝗂𝗆𝖾𝗓𝗈𝗇𝖾:** {timezone}
╰➢ **𝖲𝗎𝗇𝗋𝗂𝗌𝖾:** {sunrise}
╰➢ **𝖲𝗎𝗇𝗌𝖾𝗍:** {sunset}
╰➢ **𝖶𝗂𝗇𝖽:** {wind}
╰➢ **𝖳𝖾𝗆𝗉𝖾𝗋𝖺𝗍𝗎𝗋𝖾:** {temperature}°C
╰➢ **𝖥𝖾𝖾𝗅𝗌 𝗅𝗂𝗄𝖾:** {feels_like}°C
╰➢ **𝖬𝗂𝗇𝗂𝗆𝗎𝗆:** {temp_min}°C
╰➢ **𝖬𝖺𝗑𝗂𝗆𝗎𝗆:** {temp_max}°C
╰➢ **𝖯𝗋𝖾𝗌𝗌𝗎𝗋𝖾:** {pressure} hPa
╰➢ **𝖧𝗎𝗆𝗂𝖽𝗂𝗍𝗒:** {humidity}%
╰➢ **𝖵𝗂𝗌𝗂𝖻𝗂𝗅𝗂𝗍𝗒:** {visibility} m
╰➢ **𝖢𝗅𝗈𝗎𝖽𝗌:** {clouds}%
╰────────────────•
"""
]

AIR_POLLUTION_TEMPLATES = [
    """
🌆 {city_name}

╭────────────────•
╰➢ **𝖠𝖰𝖨:** {aqi}
╰➢ **𝖢𝖺𝗋𝖻𝗈𝗇 𝖬𝗈𝗇𝗈𝗑𝗂𝖽𝖾:** {co}
╰➢ **𝖭𝗈𝗂𝗍𝗋𝗈𝗀𝖾𝗇 𝖬𝗈𝗇𝗈𝗑𝗂𝖽𝖾:** {no}
╰➢ **𝖭𝗂𝗍𝗋𝗈𝗀𝖾𝗇 𝖣𝗂𝗈𝗑𝗂𝖽𝖾:** {no2}
╰➢ **𝖮𝗓𝗈𝗇𝖾:** {o3}
╰➢ **𝖲𝗎𝗅𝗉𝗁𝗎𝗋 𝖣𝗂𝗈𝗑𝗂𝖽𝖾:** {so2}
╰➢ **𝖠𝗆𝗆𝗈𝗇𝗂𝖺:** {nh3}
╰➢ **𝖥𝗂𝗇𝖾 𝖯𝖺𝗋𝗍𝗂𝖼𝗅𝖾𝗌 (PM{sub2_5}):** {pm2_5}
╰➢ **𝖢𝗈𝖺𝗋𝗌𝖾 𝖯𝖺𝗋𝗍𝗂𝖼𝗅𝖾𝗌 (PM{sub10}):** {pm10}
╰────────────────•
"""
]

GITHUB_USER_TEMPLATES = [
    """
🍀 {username} ({git_id})

╭──────── {id_type} ────────•
╰➢ **𝖭𝖺𝗆𝖾:** [{name}]({profile_url})
╰➢ **𝖡𝗅𝗈𝗀:** {blog}
╰➢ **𝖢𝗈𝗆𝗉𝖺𝗇𝗒:** {company}
╰➢ **𝖤𝗆𝖺𝗂𝗅:** {email}
╰➢ **𝖫𝗈𝖼𝖺𝗍𝗂𝗈𝗇:** {location}
╰➢ **𝖱𝖾𝗉𝗈:** {public_repos}
╰➢ **𝖦𝗂𝗌𝗍𝗌:** {public_gists}
╰➢ **𝖥𝗈𝗅𝗅𝗈𝗐𝖾𝗋𝗌:** {followers}
╰➢ **𝖥𝗈𝗅𝗅𝗈𝗐𝗂𝗇𝗀:** {following}
╰➢ **𝖠𝖼𝖼𝗈𝗎𝗇𝗍 𝖼𝗋𝖾𝖺𝗍𝖾𝖽:** {created_at}
╰────────────────•

**💫 𝖡𝗂𝗈:** {bio}
"""
]

STATISTICS_TEMPLATES = [
    """
🍀 {name}

╭──────── 𝖢𝗁𝖺𝗇𝗇𝖾𝗅𝗌 ────────•
╰➢ **𝖳𝗈𝗍𝖺𝗅:** `{channels}`
╰➢ **𝖠𝖽𝗆𝗂𝗇:** `{ch_admin}`
╰➢ **𝖮𝗐𝗇𝖾𝗋:** `{ch_owner}`

╭──────── 𝖦𝗋𝗈𝗎𝗉𝗌 ────────•
╰➢ **𝖳𝗈𝗍𝖺𝗅:** `{groups}`
╰➢ **𝖠𝖽𝗆𝗂𝗇:** `{gc_admin}`
╰➢ **𝖮𝗐𝗇𝖾𝗋:** `{gc_owner}`

╭──────── 𝖮𝗍𝗁𝖾𝗋𝗌 ────────•
╰➢ **𝖯𝗋𝗂𝗏𝖺𝗍𝖾:** `{users}`
╰➢ **𝖡𝗈𝗍𝗌:** `{bots}`
╰➢ **𝖴𝗇𝗋𝖾𝖺𝖽 𝖬𝖾𝗌𝗌𝖺𝗀𝖾𝗌:** `{unread_msg}`
╰➢ **𝖴𝗇𝗋𝖾𝖺𝖽 𝖬𝖾𝗇𝗍𝗂𝗈𝗇𝗌:** `{unread_mention}`

⌛ **𝖳𝗂𝗆𝖾 𝖳𝖺𝗄𝖾𝗇:** `{time_taken}`
"""
]

GBAN_TEMPLATES = [
    """
╭──────── {gtype} ────────•
╰➢ **𝖵𝗂𝖼𝗍𝗂𝗆:** {name}
╰➢ **𝖲𝗎𝖼𝖼𝖾𝗌𝗌:** {success}
╰➢ **𝖥𝖺𝗂𝗅𝖾𝖽:** {failed}
╰➢ **𝖱𝖾𝖺𝗌𝗈𝗇:** {reason}
╰────────────────•
"""
]

USAGE_TEMPLATES = [
    """
**📝 𝖣𝗂𝗌𝗄 & 𝖣𝗒𝗇𝗈 𝖴𝗌𝖺𝗀𝖾:**

**➢ 𝖣𝗒𝗇𝗈 𝖴𝗌𝖺𝗀𝖾 𝖿𝗈𝗋** `{appName}`
    ◈ __{appHours}hrs {appMinutes}mins__ | __{appPercentage}%__

**➢ 𝖣𝗒𝗇𝗈 𝗋𝖾𝗆𝖺𝗂𝗇𝗂𝗇𝗀 𝗍𝗁𝗂𝗌 𝗆𝗈𝗇𝗍𝗁:**
    ◈ __{hours}hrs {minutes}mins__ | __{percentage}%__

**➢ 𝖣𝗂𝗌𝗄 𝖴𝗌𝖺𝗀𝖾:**
    ◈ __{diskUsed}GB__ / __{diskTotal}GB__ | __{diskPercent}%__

**➢ 𝖬𝖾𝗆𝗈𝗋𝗒 𝖴𝗌𝖺𝗀𝖾:**
    ◈ __{memoryUsed}GB__ / __{memoryTotal}GB__ | __{memoryPercent}%__
"""
]

USER_INFO_TEMPLATES = [
    """
**🍀 𝖴𝗌𝖾𝗋 𝖨𝗇𝖿𝗈 𝗈𝖿 {mention}:**

**➢ 𝖥𝗂𝗋𝗌𝗍 𝖭𝖺𝗆𝖾:** `{firstName}`
**➢ 𝖫𝖺𝗌𝗍 𝖭𝖺𝗆𝖾:** `{lastName}`
**➢ 𝖴𝗌𝖾𝗋𝖨𝖣:** `{userId}`

**➢ 𝖢𝗈𝗆𝗆𝗈𝗇 𝖦𝗋𝗈𝗎𝗉𝗌:** `{commonGroups}`
**➢ 𝖣𝖢-𝖨𝖣:** `{dcId}`
**➢ 𝖯𝗂𝖼𝗍𝗎𝗋𝖾𝗌:** `{totalPictures}`
**➢ 𝖱𝖾𝗌𝗍𝗋𝗂𝖼𝗍𝖾𝖽:** `{isRestricted}`
**➢ 𝖵𝖾𝗋𝗂𝖿𝗂𝖾𝖽:** `{isVerified}`
**➢ 𝖡𝗈𝗍:** `{isBot}`
**➢ 𝖡𝗂𝗈:** `{bio}`

"""
]

CHAT_INFO_TEMPLATES = [
    """
**🍀 𝖢𝗁𝖺𝗍 𝖨𝗇𝖿𝗈:**

**➢ 𝖢𝗁𝖺𝗍 𝖭𝖺𝗆𝖾:** `{chatName}`
**➢ 𝖢𝗁𝖺𝗍 𝖨𝖣:** `{chatId}`
**➢ 𝖢𝗁𝖺𝗍 𝖫𝗂𝗇𝗄:** {chatLink}
**➢ 𝖮𝗐𝗇𝖾𝗋:** {chatOwner}
**➢ 𝖣𝖢-𝖨𝖣:** `{dcId}`
**➢ 𝖬𝖾𝗆𝖻𝖾𝗋𝗌:** `{membersCount}`
**➢ 𝖠𝖽𝗆𝗂𝗇𝗌:** `{adminsCount}`
**➢ 𝖡𝗈𝗍𝗌:** `{botsCount}`
**➢ 𝖣𝖾𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇:** `{description}`

"""
]


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


async def climate_templates(**kwargs) -> str:
    template = await db.get_env(ENV.climate_template)
    if template:
        message = template
    else:
        message = random.choice(CLIMATE_TEMPLATES)
    return message.format(**kwargs)


async def airpollution_templates(**kwargs) -> str:
    template = await db.get_env(ENV.airpollution_template)
    if template:
        message = template
    else:
        message = random.choice(AIR_POLLUTION_TEMPLATES)
    return message.format(**kwargs)


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

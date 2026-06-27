# Attribution & Credits

AstralBot is a refined fork-style rebuild that combines the strongest ideas from
two prior Telegram userbot projects. This document preserves the attribution
required by their licenses (GPL-3.0 in all cases) and documents the lineage of
the design.

## Source Projects

### 1. Zelretch (https://github.com/Siamking672/Zelretch)

- **License:** GNU General Public License v3.0
- **Author / maintainer:** Siamking672
- **What we reused:**
  - The two-repo separation pattern (deploy wrapper + plugin repo).
  - The DB-backed runtime config pattern (`ENV` class with `get_env` / `set_env`
    helpers, layered on top of os env vars).
  - The multi-account assistant support pattern (DB-stored session strings).
  - The tiered permission model (Owner → Sudo → Master → Dev → Banned/Muted).
  - The `HelpMenu().add(...).info(...).done()` fluent builder pattern.
  - Live install / uninstall / load / unload plugin management commands.
  - The `initialize_git` self-updating plugin repo concept.
- **What we did NOT copy:**
  - We did not reuse the "Rin Tohsaka / Fate" theme or any of the bundled
    image assets (`hellbot_*`, `zelretch_*`).
  - We replaced the Kurigram (`pyrogram`) namespace with stock Pyrogram v2.
  - We replaced the Mongo-only database with a pluggable SQLite-default /
    Mongo-optional backend.
  - We added a per-plugin manifest protocol that the source lacks.

### 2. FoxUserbot (https://github.com/FoxUserbot/FoxUserbot)

- **License:** GNU General Public License v3.0
- **Authors:** A9FM (https://t.me/a9_fm), ArThirtyFour (https://t.me/ArThirtyFour)
- **Designer:** Nw_Off (https://t.me/nw_off)
- **What we reused:**
  - The `fox_command() + fox_sudo()` decorator idiom (re-implemented as our
    `@on_command(..., allow_sudo=True)`).
  - The `who_message()` pattern (sudo users issuing commands in groups).
  - The safe-mode auto-rescue (`os.execv` with `--safe` flag on crash).
  - The hot module load/unload via handler introspection.
  - The trilingual `LANGUAGES` dict + `get_text()` i18n pattern (we extended
    it to per-plugin manifests).
  - The single-file backup / restore concept (we ship a backup builtin).
- **What we did NOT copy:**
  - We did NOT reuse the hardcoded shared TDesktop API credentials
    (`api_id=2040, api_hash=b18441a1ff607e10a989891a5462e627`). AstralBot
    requires users to provide their own API_ID and API_HASH.
  - We did not carry over the Flask web-auth flow (we use a simpler
    `python -m astralbot.utils.gen_session` instead).
  - We did not reuse the regex-based legacy-module migration code
    (`migrate.py`, `plugin_validator.py:_convert_content`).

### 3. CustomModules (https://github.com/FoxUserbot/CustomModules)

- **License:** No top-level LICENSE file. Individual files claim AGPL-3.0 or
  are unattributed. We respect the AGPL-3.0 claims where they appear.
- **Authors (per-file headers):**
  - @codrago_m / @codrago — `PromoClaimer.py` (AGPL-3.0)
  - qq_shark — `media2gif.py` (AGPL-3.0, https://github.com/qqshark/Modules)
  - xdesai (mods.xdesai.top) — `weather_xdesai.py`, `currency.py`, `url.py`,
    `ipinfo.py`, `ToDo.py`, `stats_xdesai.py` (ported via Wine Hikka)
  - KOTmodules (https://github.com/KOTmodules/FREEmodules) — `KOTaiwaifu.py`
  - AmokDev (https://github.com/AmokDEV/lordnet) — `hearts.py` (refactored by A9FM)
  - ArThirtyFour — `premium_text.py`
- **What we reused:**
  - Module concepts (not verbatim code): AFK, QR code generator, weather,
    currency converter, Wikipedia lookup, IP info, URL expander, ToDo list,
    tagall, purge, sticker tools.
  - The trilingual `LANGUAGES` dict pattern.
- **What we did NOT copy:**
  - We did NOT carry over any of the hardcoded API keys found in the source
    repo (OpenRouter in `ai.py` and `wine_hikka.py`, Last.fm in `lastfm.py`,
    OpenWeatherMap in `weather_xdesai.py`, Genius in `find_music.py`, rule34
    in `rule34.py`, OK.ru in `telega_detector.py`). All API keys are
    user-provided via `.setvar` or env vars.
  - We did not port any of the modules with provenance / legal issues:
    `Bull.py` / `AuroraBull.py` (obscene harassment), `патриот.py`
    (political Z-symbol), `HistoryFacts.py` (politically sensitive WWII
    "facts"), `db0mb3r.py` (SMS bomber, illegal in many jurisdictions),
    `rule34.py` (NSFW content).
  - We did not port `wine_hikka.py` (AI module porter) — the OpenRouter API
    key dependency was unacceptable, and the AI-ported code was unreliable.

## License of AstralBot

AstralBot is licensed under the **GNU General Public License v3.0** — the same
license as both source projects. See [LICENSE](LICENSE) for the full text.

This means you may freely use, modify, and redistribute AstralBot, **including
commercially**, provided that:

1. You preserve this license and attribution notice in all copies.
2. You make the source code of any modified version available under the same
   license.
3. You do not impose additional restrictions on recipients' rights under the GPL.

## Third-Party Libraries

AstralBot depends on the following open-source libraries (see
`requirements.txt` for full list with versions):

| Library | License |
|---------|---------|
| Pyrogram | LGPL-3.0-or-later |
| TgCrypto | LGPL-3.0-or-later |
| aiosqlite | MIT |
| motor | Apache-2.0 |
| python-dotenv | BSD-3-Clause |
| aiohttp | Apache-2.0 |
| requests | Apache-2.0 |
| Pillow | HPND (MIT-CMU) |
| psutil | BSD-3-Clause |
| pytz | MIT |

## Contributing

If you contribute to AstralBot, you agree that your contributions will be
licensed under the same GPL-3.0 license as the rest of the project. Please add
yourself to the contributors list below in your first PR.

## Contributors

- AstralBot Team — initial refined fork-style rebuild combining Zelretch and
  FoxUserbot design ideas.

## Reporting Issues

For bugs, feature requests, or security disclosures, please open an issue on
the [AstralBot GitHub repository](https://github.com/AstralBot/AstralBot/issues).

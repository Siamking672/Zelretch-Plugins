---
title: AstralBot
emoji: ✨
colorFrom: indigo
colorTo: purple
sdk: docker
app_file: Dockerfile
pinned: false
license: gpl-3.0
python_version: "3.11"
---

# ✨ AstralBot

> A refined Telegram userbot framework combining the strongest ideas from
> [Zelretch](https://github.com/Siamking672/Zelretch) and
> [FoxUserbot](https://github.com/FoxUserbot/FoxUserbot) into a single,
> polished, developer-friendly codebase.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pyrogram v2](https://img.shields.io/badge/Pyrogram-v2-orange.svg)](https://docs.pyrogram.org/)

---

## Table of Contents

- [Overview](#overview)
- [The 1-command deploy](#the-1-command-deploy)
- [How the setup wizard works](#how-the-setup-wizard-works)
- [Architecture](#architecture)
- [Deployment targets](#deployment-targets)
  - [Local / venv](#local--venv)
  - [Docker](#docker)
  - [VPS (systemd)](#vps-systemd)
- [Configuration](#configuration)
- [Built-in commands](#built-in-commands)
- [Plugin system](#plugin-system)
- [Plugin repository](#plugin-repository)
- [Credits & license](#credits--license)

---

## Overview

AstralBot is a **Telegram userbot** — a bot framework that runs on your own
personal Telegram account (not a BotFather bot). It listens for commands
prefixed with `.` (configurable) and executes them on your behalf: manage
groups, fetch media, run shell commands, reply when you're AFK, and hundreds
more.

AstralBot is **not** a fork of either source project — it's a **refined
rebuild** that picks the best architectural ideas from both:

| Source project | Best idea we kept |
|---|---|
| **Zelretch** (a retheme of Hellbot) | Two-repo separation, DB-backed runtime config (`ENV` class), multi-account assistants, tiered permissions, `HelpMenu` fluent builder, live plugin install/uninstall |
| **FoxUserbot** | `fox_command()` decorator idiom, safe-mode auto-rescue, hot module load/unload, trilingual i18n pattern, single-file backup/restore, **web-based first-launch auth** |

## The 1-command deploy

No env vars, no Procfile, no app.json. Just:

```bash
git clone https://github.com/AstralBot/AstralBot.git
cd AstralBot
pip install -r requirements.txt
python -m astralbot
```

That's it. The first time you run `python -m astralbot`:

1. **A web browser opens automatically** to `http://localhost:8080`.
2. You fill in a form with your API credentials.
3. Click **Next** → optionally create a userbot session (you can skip this).
4. Click **Deploy** → the wizard writes `.env` and starts the bot.

The bot is then running in the background. Press `Ctrl+C` in the wizard
terminal to exit (the bot keeps running).

To re-run the wizard later:

```bash
python -m astralbot.setup
```

## How the setup wizard works

The wizard is a tiny Flask app. It auto-detects its environment:

- **Local** — binds to `http://127.0.0.1:8080`, auto-opens your browser
- **HuggingFace Spaces** — binds to `0.0.0.0:$PORT` (default 7860), accessible via the Space URL

It has three pages:

### Page 1 — Required + optional config

| Field | Required? | Notes |
|---|---|---|
| `API_ID` | ✅ | From <https://my.telegram.org/apps> |
| `API_HASH` | ✅ | From <https://my.telegram.org/apps> |
| `BOT_TOKEN` | optional | From [@BotFather](https://t.me/BotFather) — needed if you want to skip session creation |
| `HANDLERS` | optional | Default `. !` (space-separated prefixes) |
| `DATABASE_URL` | optional | MongoDB URI; if blank, SQLite is used (zero-config) |
| `LOG_CHAT_ID` | optional | Telegram chat ID for log forwarding |
| `PLUGIN_REPO` | optional | Default `AstralBot/AstralModules` |

### Page 2 — Userbot session (skippable)

Three options:

- **Option A — Create a new session interactively.** Enter your phone
  number → Telegram sends a login code → enter the code → (if 2FA enabled)
  enter your password → done. The session string is generated server-side
  and saved to `.env`.
- **Option B — Paste an existing session string.** If you already have one
  (e.g. generated with `python -m astralbot.utils.gen_session`), paste it.
- **Option C — Skip.** You can do it later from inside the bot by DMing it
  `.session`. **Note:** if you skip AND didn't provide a `BOT_TOKEN` in
  page 1, the bot cannot start (it needs at least one client credential).

### Page 3 — Review + Deploy

Review the collected config, then click **🚀 Deploy AstralBot**. The wizard:

1. Writes `.env` with the collected vars.
2. Starts `python -m astralbot --no-wizard` in a detached subprocess.
3. Shows a success page.

The wizard process exits after deploy. The bot continues running in the
subprocess — you'll see its log output in the same terminal where the
wizard was running.

### Doing it later via `.session`

If you skipped session creation in the wizard, the bot starts in
**assistant-bot mode** (using your `BOT_TOKEN`). To add a userbot session
later:

1. DM your assistant bot `.session`
2. The bot replies asking for your phone number
3. Reply with `+15551234567`
4. The bot sends a login code request — reply with the code
5. (If 2FA) Reply with your cloud password
6. The bot saves the session to `.env` and the database
7. Run `.restart` to enable userbot mode

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  AstralBot (this repo) — main deployable project             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  astralbot/                                          │    │
│  │    __main__.py        ← entry point:                 │    │
│  │                          if no .env → wizard         │    │
│  │                          else → start bot            │    │
│  │    setup_wizard.py    ← Flask 3-page wizard          │    │
│  │    setup.py           ← `python -m astralbot.setup`  │    │
│  │    core/              ← framework (config, db, etc.) │    │
│  │    helpers/           ← shared utility functions     │    │
│  │    plugins/           ← decorator + help registry    │    │
│  │      builtins/        ← always-on commands           │    │
│  │    utils/gen_session  ← standalone session generator │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  At startup, the loader scans THREE plugin roots:            │
│    1. astralbot/plugins/builtins/ (always loaded)            │
│    2. userdata/plugins/             (user-installed)         │
│    3. userdata/external_plugins/    (pulled from             │
│                                     PLUGIN_REPO at startup)  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  AstralModules (separate repo) — external plugin repository  │
│                                                              │
│  modules/                                                    │
│    admin/   — promote, ban, kick, mute, pin, purge, lock     │
│    utils/   — afk, notes, filters, warns, greetings, snips  │
│    media/   — download, upload, sticker, songs, telegraph    │
│    ai/      — LLM chat, TTS, ASR                             │
│    fun/     — quote, whois, weather, currency, wikipedia     │
│    privacy/ — pmpermit, antipin, antichannel, blacklist      │
└──────────────────────────────────────────────────────────────┘
```

The two repos are **completely separate**. The main project downloads the
plugin repo as a zip at startup (or on `.update`) and loads it from
`userdata/external_plugins/`. You can swap plugin repos by changing the
`PLUGIN_REPO` env var.

## Deployment targets

### HuggingFace Spaces (recommended for free 24/7 hosting)

AstralBot ships with a HuggingFace Spaces Dockerfile and YAML front-matter
in the README — push the repo to a new Docker Space and it just works.

1. Create a new HuggingFace Space at <https://huggingface.co/new-space>:
   - **SDK:** Docker
   - **License:** GPL-3.0
   - **Hardware:** CPU basic (free) is enough
   - **Persistent storage:** recommended (so your `.env` and SQLite DB
     survive container restarts)

2. Push the AstralBot code to the Space (via `git push` or the HF web UI).

3. The Space builds the Docker image and starts the wizard. Visit the
   Space URL (e.g. `https://yourname-astralbot.hf.space/`) — you'll see
   the setup wizard.

4. Fill in API_ID, API_HASH, optionally BOT_TOKEN. Skip session creation
   if you want (you can do it later via `.session`).

5. Click **🚀 Deploy AstralBot**. The wizard starts the bot in a
   background thread within the same process, so the Space keeps
   responding to health checks.

6. Visit `/status` to see the bot's running state, or `/health` for a
   JSON status.

**Notes on HF Spaces:**
- The wizard auto-detects HF Spaces via the `SPACE_ID` env var (set by HF
  on every Space). It then binds to `0.0.0.0:$PORT` (HF default 7860)
  instead of `127.0.0.1:8080`.
- The `.env` file is written to `/data/.env` if persistent storage is
  enabled, otherwise to `userdata/.env` (which is ephemeral — config
  will be lost on container restart without persistent storage).
- The bot runs in a daemon thread inside the Flask process. If the bot
  crashes, the Space stays up — you can re-run the wizard by removing
  `/data/.env` (or by setting the env vars via HF Space Secrets instead).
- For maximum reliability, set your `API_ID`, `API_HASH`,
  `STRING_SESSION` (or `BOT_TOKEN`) as HF Space Secrets — they'll be
  injected as env vars at container start, bypassing the wizard entirely.

### Local / venv

The simplest path — works on any OS with Python 3.11+:

```bash
git clone https://github.com/AstralBot/AstralBot.git
cd AstralBot
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m astralbot
```

The wizard launches automatically on first run. Open the URL it prints
(usually <http://localhost:8080>) in your browser.

### Docker

```bash
git clone https://github.com/AstralBot/AstralBot.git
cd AstralBot
docker compose up --build -d
```

This starts the container in the background. The wizard port (7860) is
mapped to your host. Open <http://localhost:7860> in your browser to
complete setup.

Once you've deployed via the wizard, the `.env` file is created in
`./userdata/.env` (bind-mounted), so it persists across container rebuilds.

To view logs:

```bash
docker compose logs -f
```

To stop:

```bash
docker compose down
```

**Note:** to simulate HuggingFace Spaces locally (bind to 0.0.0.0:7860),
set `SPACE_ID=yourname/astralbot` in your `.env` or `docker-compose.yml`.

### VPS (systemd)

For 24/7 hosting on a Linux VPS:

```bash
sudo bash install.sh
```

The install script:
- Creates a non-root `astralbot` system user
- Installs to `/opt/astralbot` (clones / pulls as needed)
- Sets up a Python venv at `/opt/astralbot/venv`
- Installs the systemd unit (`astralbot.service`)
- Enables the service (does NOT auto-start — you need to set up `.env` first)

After install, choose one of two paths:

**Path A — Interactive wizard (recommended):**

```bash
sudo -u astralbot /opt/astralbot/venv/bin/python -m astralbot
```

The wizard runs on `http://localhost:8080` — SSH-tunnel or use a port
forwarder to access it from your browser. After deploy:

```bash
sudo systemctl start astralbot
```

**Path B — Manual `.env` file:**

```bash
sudo -u astralbot nano /opt/astralbot/.env
# Fill in API_ID, API_HASH, STRING_SESSION (or BOT_TOKEN)
sudo systemctl start astralbot
```

To generate a session string manually:

```bash
sudo -u astralbot /opt/astralbot/venv/bin/python -m astralbot.utils.gen_session
```

Common systemd commands:

```bash
sudo systemctl status astralbot
sudo journalctl -u astralbot -f
sudo systemctl restart astralbot
sudo systemctl stop astralbot
```

## Configuration

AstralBot supports two layers of configuration:

### 1. Static config (`.env` file or env vars)

See [`.env.example`](.env.example) for the full list with comments.
Required:

| Var | Description |
|---|---|
| `API_ID` | Telegram API ID from <https://my.telegram.org/apps> |
| `API_HASH` | Telegram API hash from <https://my.telegram.org/apps> |
| `STRING_SESSION` **or** `BOT_TOKEN` | At least one is required to start a client |

### 2. Runtime config (DB-backed)

In addition to env vars, AstralBot supports **runtime config vars** stored
in the database. These can be changed from Telegram without redeploying:

```
.setvar PING_TEMPLATE ✨ Custom Pong!
.getvar PING_TEMPLATE
.delvar PING_TEMPLATE
.listvar
```

This is the strongest idea from Zelretch's `ENV` class — tunable settings
(templates, API keys, feature toggles) live in the DB while static
credentials stay in `.env`.

## Built-in commands

These are always loaded from `astralbot/plugins/builtins/`:

| Command | Permission | Description |
|---|---|---|
| `.ping` | sudo | Check bot-to-Telegram latency |
| `.alive` | sudo | Show bot status (version, uptime, plugin count) |
| `.info` | sudo | Show system + deployment info |
| `.help` | sudo | Show all available commands |
| `.plinfo` | sudo | List loaded plugins with metadata |
| `.cmdinfo <cmd>` | sudo | Show details for a single command |
| `.session` | owner | Interactively create a userbot session (for wizard-skippers) |
| `.cancel` | owner | Cancel an in-progress `.session` flow |
| `.eval <code>` | owner | Execute Python code |
| `.sh <cmd>` | owner | Run a shell command |
| `.restart` | owner | Restart the bot process |
| `.shutdown` | owner | Shut down the bot |
| `.update` | owner | Pull latest plugins and restart |
| `.load <name>` | owner | Load a plugin by name |
| `.unload <name>` | owner | Unload a plugin by name |
| `.reload <name>` | owner | Reload a plugin by name |
| `.install <name>` | owner | Install a plugin from a replied `.py` file |
| `.uninstall <name>` | owner | Uninstall a plugin (deletes its file) |
| `.list` | sudo | List all loaded plugins |
| `.getvar <key>` | owner | Read a runtime config var |
| `.setvar <key> <val>` | owner | Set a runtime config var |
| `.delvar <key>` | owner | Delete a runtime config var |
| `.listvar` | owner | List all runtime config vars |
| `.prefix` | sudo | Show current command prefixes |
| `.addmaster` | owner | Add a master user (sudo tier) |
| `.delmaster` | owner | Remove a master user |
| `.masters` | owner | List master users |
| `.whoami` | public | Show your permission tier |

## Plugin system

### Plugin discovery

The loader scans three roots at startup:

1. **`astralbot/plugins/builtins/`** — always loaded, ships with the main project.
2. **`userdata/plugins/`** — user-installed plugins (via `.install`).
3. **`userdata/external_plugins/modules/`** — pulled from `PLUGIN_REPO` at startup or via `.update`.

In **safe mode** (auto-triggered after a startup crash), only root #1 is loaded.

### Plugin contract

A plugin is any `.py` file. It MAY declare module-level manifest attributes
(recommended):

```python
__plugin_name__        = "Admin Tools"
__plugin_author__      = "Your Name"
__plugin_version__     = "1.0.0"
__plugin_license__     = "GPL-3.0"
__plugin_description__ = "Group administration commands."
__plugin_category__    = "admin"
__plugin_deps__        = []            # optional pip deps
__plugin_min_core__    = "1.0.0"       # minimum AstralBot version
```

Commands are registered via the `@on_command` decorator:

```python
from astralbot import on_command, help_menu

@on_command("hello", description="Say hello", permission="sudo")
async def hello_cmd(client, message):
    await message.edit_text("Hello, world!")

# Or auto-register help via the fluent builder:
help_menu.add(
    command="hello",
    args=None,
    description="Say hello.",
    example=".hello",
    category="fun",
    plugin="hello",
).register()
```

For non-command watchers (AFK auto-reply, antiflood, pmpermit):

```python
from astralbot import on_event
from pyrogram import filters

@on_event(filters.incoming & filters.private)
async def my_watcher(client, message):
    ...
```

### Permission tiers

The `permission` arg on `@on_command` accepts:

| Value | Who can run it |
|---|---|
| `public` | Anyone |
| `sudo` | Owner + sudo users + DB masters + devs |
| `dev` | Owner + sudo + devs (NOT masters) |
| `owner` | Only the owner |

### Multi-account support

The `@on_command` and `@on_event` decorators automatically register handlers
on **every** active client. If you've added extra sessions to the database
(via the assistant bot's session-management commands), they will all receive
the command.

## Plugin repository

The official external plugin repository is **[AstralBot/AstralModules](https://github.com/AstralBot/AstralModules)**.
It is pulled automatically at startup (or via `.update`) into
`userdata/external_plugins/modules/`.

The plugin repo is organized by category:

```
modules/
  admin/    — promote, demote, ban, kick, mute, pin, purge, lock, federation
  utils/    — afk, notes, filters, warns, greetings, snips, antiflood
  media/    — download, upload, sticker, songs, telegraph, qr, convert
  ai/       — llm (OpenRouter/Gemini), tts, asr
  fun/      — quote, whois, weather, currency, wikipedia, animate
  privacy/  — pmpermit, antipin, antichannel, firstmsg, blacklist
```

To use a **different** plugin repo, set `PLUGIN_REPO` in `.env` (or via the
wizard), or use `.setvar PLUGIN_REPO YourName/YourModules` followed by `.update`.

To install individual plugins, reply to a `.py` file with `.install <name>`.

## Credits & license

AstralBot is licensed under the **GNU General Public License v3.0** — the same
license as both source projects. See [LICENSE](LICENSE) for the full text and
[ATTRIBUTION.md](ATTRIBUTION.md) for detailed credits to:

- **Siamking672** — Zelretch and Zelretch-Plugins
- **A9FM** (https://t.me/a9_fm) — FoxUserbot
- **ArThirtyFour** (https://t.me/ArThirtyFour) — FoxUserbot
- **Nw_Off** (https://t.me/nw_off) — FoxUserbot design
- Various CustomModules contributors (per-file attribution in ATTRIBUTION.md)

## Differences from the source projects

See [ATTRIBUTION.md](ATTRIBUTION.md) for the full breakdown. Summary:

1. **1-command deploy.** AstralBot's setup wizard launches with
   `python -m astralbot` — no env vars, no Procfile, no app.json. Neither
   source project had anything quite like this (FoxUserbot had a Flask
   web-auth flow but it was only for session creation, not full config).
2. **Stricter config validation.** AstralBot hard-fails on missing required
   env vars. Zelretch silently produced `0`/`None`; FoxUserbot shipped shared
   hardcoded TDesktop API credentials.
3. **Pluggable database.** SQLite by default (zero-config), MongoDB optional.
   Zelretch was Mongo-only; FoxUserbot had no DB at all.
4. **Per-plugin manifests.** AstralBot plugins declare `__plugin_name__`,
   `__version__`, `__author__`, etc. Neither source had this.
5. **No bundled API keys.** All API keys are user-provided. CustomModules
   shipped live OpenRouter / Last.fm / Genius / rule34 / OK.ru keys in public
   source — we refused to carry these over.
6. **No legally/ethically risky modules.** We did not port the SMS bomber,
   the political Z-symbol generator, the WWII "facts" generator, the obscene
   trash-talk generators, or the NSFW rule34 module.
7. **Pinned dependencies.** All Python deps are pinned in `requirements.txt`
   for reproducible builds. Both source projects left almost everything
   unpinned.
8. **Stock Pyrogram v2.** We use stock Pyrogram v2 instead of the Kurigram
   drop-in fork, for long-term maintainability.
9. **Three deploy targets only.** Docker, VPS (systemd), and local venv.
   We removed Heroku / Railway / Render support to keep the deploy story
   simple — the 1-command wizard replaces them all.

---

<p align="center">
  Built with care, for the community.<br>
  Star ⭐ the repo if you find it useful.
</p>

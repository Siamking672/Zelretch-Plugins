---
title: Zelretch
emoji: 🗡️
colorFrom: red
colorTo: purple
sdk: docker
pinned: false
license: gpl-3.0
---

# Zelretch

Docker-friendly deployment wrapper for **Zelretch Plugins**, a Fate-inspired, Rin Tohsaka-themed Telegram userbot.

This repository ships a **one-command web-based deployment wizard**. You no longer need to edit `.env` files by hand — the wizard collects every variable through a clean browser UI, saves the configuration to your MongoDB database so future deployments can be restored, and then starts the bot.

## One-command deploy

```bash
./setup
```

Or, if you prefer to skip the bash wrapper:

```bash
python deploy.py
```

The wizard:

1. Opens a local web page (default <http://127.0.0.1:8765>).
2. Walks you through required variables (API_ID, API_HASH, BOT_TOKEN, OWNER_ID, LOGGER_ID, DATABASE_URL, ...).
3. Optionally creates a userbot session via an OTP flow (or accepts an existing session string, or lets you skip entirely).
4. Saves the configuration to MongoDB so the next deployment can be restored from just the database URL.
5. Downloads the plugin repository, installs its dependencies, and starts `python -m zelretch`.

## Restore from a previous deployment

If you have deployed Zelretch before, open the wizard and choose **Restore from Database**. Enter only your MongoDB URL — the wizard fetches the saved configuration and takes you straight to the deploy button.

## Required variables

The wizard collects (and validates) the following:

| Variable | Required | Description |
|---|---|---|
| `API_ID` | yes | Telegram API ID from <https://my.telegram.org> |
| `API_HASH` | yes | Telegram API hash from <https://my.telegram.org> |
| `BOT_TOKEN` | yes | Assistant bot token from [@BotFather](https://t.me/BotFather) |
| `OWNER_ID` | yes | Your numeric Telegram user ID |
| `LOGGER_ID` | yes | A group/channel where the bot is admin (negative for groups) |
| `DATABASE_URL` | yes | MongoDB connection string |
| `DATABASE_NAME` | optional | Defaults to `Zelretch` |
| `HANDLERS` | optional | Command prefixes; defaults to `. ! ?` |
| `PLUGINS_REPO` | optional | Defaults to `Siamking672/Zelretch-Plugins` |
| `PLUGINS_BRANCH` | optional | Defaults to `main` |
| `SESSION_STRING` | optional | Pyrogram session string for the userbot (skip if you only want the assistant bot) |

## Architecture

The project is split into two repositories:

| Repository | Role |
|---|---|
| `Siamking672/Zelretch` (this repo) | Deployment wizard + Docker wrapper. Downloads and runs the plugin repo at runtime. |
| `Siamking672/Zelretch-Plugins` | Plugin archive (`zelretch/` Python package). Loaded by the main wrapper. |

The wizard lives in `deploy/` and is a small Flask application:

```
deploy/
├── server.py            # Flask app + routes
├── orchestrator.py      # Deployment step runner (validate → connect → save → install → start)
├── storage.py           # MongoDB-backed config persistence
├── validators.py        # Form-field validation
├── session_helper.py    # Interactive userbot OTP flow
├── templates/           # Jinja2 templates (intro, restore, required, userbot, review, status)
└── static/              # CSS + JS (Fate/Rin Tohsaka theme, SSE client)
```

Deployment steps shown on the status screen:

1. Validating variables
2. Connecting to database
3. Saving configuration
4. Generating `.env`
5. Installing dependencies
6. Downloading plugin repository
7. Storing userbot session (skipped if no session)
8. Starting Zelretch

If any step fails, the wizard shows the error in the UI with a Retry button — no need to start over from scratch.

## Local deployment

```bash
git clone https://github.com/Siamking672/Zelretch.git
cd Zelretch
python deploy.py
```

## Docker deployment

```bash
docker compose up --build -d
```

The wizard listens on `0.0.0.0:8765` inside the container. After `docker compose up`, open <http://localhost:8765> in your browser.

To view logs:

```bash
docker compose logs -f
```

To stop:

```bash
docker compose down
```

## Hugging Face Space deployment

This repository is configured as a Docker Space through the YAML block at the top of this README. The wizard auto-detects the HF environment via the `SPACE_AUTHOR_NAME` / `SPACE_REPO_NAME` env vars that HF injects into every Space container, and adapts accordingly:

| Setting | Local / VPS Docker | Hugging Face Space |
|---|---|---|
| Listen host | `127.0.0.1` (or `ZELRETCH_WIZARD_HOST`) | `0.0.0.0` (HF requires this) |
| Listen port | Free port in `8765..8785` | `7860` (HF's only exposed port) |
| Public URL | `http://localhost:8765` | `https://{author}-{repo}.hf.space` |
| Auto-open browser | Yes | No (no GUI in container) |

### First-time setup on Hugging Face

1. Create a new Docker Space on Hugging Face.
2. Push this repository's contents to the Space's Git repo (or use the GitHub integration to mirror).
3. Wait for the build to finish (check the "Logs" tab in the HF UI).
4. Open the Space's public URL — `https://{author}-{repo}.hf.space` — in your browser.
5. The wizard's intro page loads. Click **New Deployment**, fill in the required variables, optionally configure a userbot session, then click **Deploy**.

### Auto-deploy on HF Space restarts (fully automatic)

Hugging Face Spaces rebuild and restart the container on every Git push, and free-tier Spaces sleep after 48 hours of inactivity. To make the bot come back online **completely automatically** — no manual interaction required:

1. Do your first deployment manually via the wizard (fill in all variables, click Deploy).
2. The wizard saves your configuration to MongoDB automatically during deployment.
3. Go to your Space's **Settings → Repository secrets**.
4. Add a secret named `DATABASE_URL` with your MongoDB connection string.
5. (Optional) Add `DATABASE_NAME=Zelretch` as well.

From now on, every time the Space restarts (Git push, sleep wake-up, manual restart):

1. The wizard detects `DATABASE_URL` in the environment.
2. Connects to MongoDB and fetches the saved configuration.
3. Verifies all 6 required variables are present.
4. **Automatically starts the deployment** — downloads plugins, installs deps, starts the bot.
5. The bot comes back online on its own. You don't need to visit the wizard URL at all.

If you do visit the wizard URL during an auto-deploy, you'll see the deployment progress on the status page. If the auto-deploy fails (e.g. MongoDB is unreachable), the wizard shows the error and a Retry button.

**Note:** If the saved config is missing any required variable, auto-deploy is skipped and the wizard shows the review page for manual deployment instead.

## Security

- The wizard listens on `127.0.0.1` locally (or `0.0.0.0:7860` on Hugging Face Spaces, behind HF's reverse proxy).
- Sensitive values (BOT_TOKEN, API_HASH, DATABASE_URL, SESSION_STRING) are never echoed back in full — the review screen masks them.
- Configuration is stored in MongoDB under a `deployment_config` collection. Session strings are stored in the bot's own `session` collection (the runtime expects this).
- The wizard scrubs `KEY=value` lines from error/log output before streaming it to the browser.
- The generated `.env` file is created with `0600` permissions on Unix-like systems.
- On Hugging Face, use **Repository secrets** (not plaintext env vars) for `DATABASE_URL` — secrets are encrypted at rest and only decrypted inside the container.

## Notes

- Kurigram is installed through the `kurigram` package. The code keeps `from pyrogram ...` imports because Kurigram is a drop-in replacement that exposes the Pyrogram-compatible namespace.
- The GPL license file is retained.

## Theme

This build uses a Rin Tohsaka / Fate-style fan theme for startup cards, menus, buttons, and bot status text. It is not affiliated with the Fate franchise.

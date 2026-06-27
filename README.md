---
title: Zelretch Plugins
emoji: 💎
colorFrom: red
colorTo: purple
sdk: docker
pinned: false
license: gpl-3.0
---

# Zelretch Plugins

Fate-inspired, Rin Tohsaka-themed plugin archive for the Zelretch userbot.

Plugin source repository for **Zelretch**.

The main wrapper repository downloads this repo by default:

```text
Siamking672/Zelretch-Plugins
```

## Runtime stack

- Python 3.11
- Kurigram installed through `kurigram`
- Pyrogram-compatible import namespace: `from pyrogram ...`
- MongoDB through Motor
- Docker-only deployment

## Required variables

```env
API_HASH=
API_ID=
BOT_TOKEN=
DATABASE_URL=
LOGGER_ID=
OWNER_ID=
```

Optional:

```env
DATABASE_NAME=Zelretch
HANDLERS=. ! ?
PLUGINS_REPO=Siamking672/Zelretch-Plugins
PLUGINS_BRANCH=main
```

## Hugging Face Space deployment

This repository is configured as a Docker Space through the YAML block at the top of this README.

Use Hugging Face **Repository secrets** for runtime values:

```env
API_HASH=
API_ID=
BOT_TOKEN=
DATABASE_URL=
LOGGER_ID=
OWNER_ID=
```

For the main wrapper, the default plugin source is:

```text
Siamking672/Zelretch-Plugins
```

Docker Spaces build from the root `Dockerfile`; `docker-compose.yml` is for local/VPS deployment only.

## Docker deployment

```bash
cp example.env .env
nano .env
docker compose up --build -d
```

View logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

## Plugin template

```python
from . import HelpMenu, on_message, zelretch


@on_message("hii")
async def hi(_, message):
    await zelretch.edit(message, "Hello!")


HelpMenu("hii").add(
    "hii", None, "Says hello."
).done()
```


## Notes

- The GPL license file is retained.

## Theme

This build uses a Rin Tohsaka / Fate-style fan theme for startup cards, menus, buttons, and bot status text. It is not affiliated with the Fate franchise.

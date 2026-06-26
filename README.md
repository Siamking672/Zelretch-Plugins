---
title: Jeweled Sword Zelretch
emoji: 🗡️
colorFrom: purple
colorTo: indigo
sdk: docker
pinned: false
license: gpl-3.0
---

# Jeweled Sword Zelretch

Docker-only deployment wrapper for **Jeweled Sword Zelretch Plugins**.

This repository intentionally stays small. It downloads the plugin repository at container startup and runs the bot from that source tree.

## Default plugin repository

```text
Siamking672/Jeweled-Sword-Zelretch-Plugins
```

Override it with `PLUGINS_REPO` or `PLUGINS_ZIP_URL` when needed.

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
DATABASE_NAME=JeweledSwordZelretch
HANDLERS=. ! ?
PLUGINS_REPO=Siamking672/Jeweled-Sword-Zelretch-Plugins
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
Siamking672/Jeweled-Sword-Zelretch-Plugins
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

## Notes

- Kurigram is installed through the `kurigram` package. The code keeps `from pyrogram ...` imports because Kurigram is a drop-in replacement that exposes the Pyrogram-compatible namespace.
- The GPL license file is retained.

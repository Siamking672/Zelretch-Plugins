#!/usr/bin/env python3
"""Zelretch one-command deployment wizard.

Run::

    python deploy.py

This starts a Flask server hosting the wizard UI. The wizard guides the
user through:

  1. Choosing a new deployment or restoring from an existing database.
  2. Entering all required variables (API_ID, API_HASH, BOT_TOKEN, ...).
  3. Optionally creating or pasting a userbot session string.
  4. Reviewing the configuration and clicking *Deploy*.
  5. Watching real-time deployment progress.

The wizard process exits after the bot has been started; the bot then
takes over the terminal/container and runs as usual.

Environment detection
---------------------

The wizard automatically detects three deployment contexts:

* **Local** (laptop, VPS, plain Docker) — listens on ``127.0.0.1``,
  auto-opens the user's browser, picks any free port in ``8765..8785``.

* **Hugging Face Space** (detected via ``SPACE_AUTHOR_NAME`` and
  ``SPACE_REPO_NAME`` env vars) — listens on ``0.0.0.0:7860`` (HF's
  only exposed port), skips browser auto-open, prints the public
  ``hf.space`` URL in the banner.

* **Auto-resume** — if ``DATABASE_URL`` is set (e.g. via an HF Space
  secret) AND a saved configuration is found in that database, the
  wizard bootstraps the in-memory state from the saved config so the
  user can hit *Deploy* immediately on a container restart.
"""

from __future__ import annotations

import asyncio
import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path


# ---------------------------------------------------------------------------
# CRITICAL: Make the project root importable BEFORE any other import that
# might transitively pull in `kurigram` (our shim package).
#
# When this file is run as ``python deploy.py``, Python adds deploy.py's
# parent directory to sys.path automatically. But when run via ``python
# -m deploy`` or inside certain containers (Hugging Face Spaces), that
# automatic insertion doesn't always happen early enough. We do it
# explicitly here so the ``kurigram/`` shim package is findable by every
# subsequent import — including inside _ensure_deps() and inside the
# deploy.* submodules.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------

def _is_huggingface_space() -> bool:
    """True if running inside a Hugging Face Space.

    HF injects ``SPACE_AUTHOR_NAME`` and ``SPACE_REPO_NAME`` into every
    Space container. We use the presence of both as a reliable signal.
    """
    return bool(os.environ.get("SPACE_AUTHOR_NAME")) and bool(
        os.environ.get("SPACE_REPO_NAME")
    )


def _hf_space_url() -> str | None:
    """Return the public URL of this Hugging Face Space, or ``None``.

    Pattern: ``https://{author}-{repo}.hf.space``. HF lowercases the
    full name and replaces underscores with hyphens.
    """
    author = os.environ.get("SPACE_AUTHOR_NAME")
    repo = os.environ.get("SPACE_REPO_NAME")
    if not author or not repo:
        return None
    # HF converts the author/repo to lowercase and replaces underscores.
    slug = f"{author}-{repo}".replace("_", "-").lower()
    return f"https://{slug}.hf.space"


def _resolve_host_and_port() -> tuple[str, int]:
    """Pick the listen host and port for the current environment.

    * Hugging Face Space -> ``0.0.0.0`` and the ``PORT`` env var (HF
      sets this to ``7860`` by default; we honour any override).
    * Local / Docker     -> ``127.0.0.1`` (override with
      ``ZELRETCH_WIZARD_HOST``) and a free port in ``8765..8785``.
    """
    if _is_huggingface_space():
        host = "0.0.0.0"
        port = int(os.environ.get("PORT", "7860"))
        return host, port

    host = os.environ.get("ZELRETCH_WIZARD_HOST", "127.0.0.1")
    # Find a free port in the 8765..8785 range.
    for candidate in range(8765, 8786):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, candidate))
                return host, candidate
        except OSError:
            continue
    raise RuntimeError("No free port in range 8765-8785")


def _detect_lan_ip() -> str | None:
    """Return the host's primary LAN IPv4 address, or ``None``.

    Used purely for the banner — we open a UDP socket to a public IP
    (no packets are actually sent) so the kernel picks the right
    source interface, then read it back.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


def _ensure_deps() -> None:
    """Best-effort install of wizard deps if the user is running the
    script for the first time on a fresh machine."""
    try:
        import flask  # noqa: F401
        import motor  # noqa: F401
        # Don't `import kurigram` here — the shim imports pyrogram,
        # and if pyrogram isn't installed yet this would cache a
        # failed import in sys.modules. Just check for the underlying
        # pyrogram package (which kurigram installs as).
        import pyrogram  # noqa: F401
    except ImportError:
        print("Installing wizard dependencies...")
        import subprocess
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--root-user-action=ignore",
                 "-r", str(_PROJECT_ROOT / "requirements.txt")]
            )
        except subprocess.CalledProcessError as exc:
            print(f"Failed to install wizard dependencies: {exc}")
            raise SystemExit(1)


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def _print_banner(host: str, port: int) -> None:
    """Print a friendly, context-aware list of URLs.

    * On Hugging Face Spaces we print the public ``hf.space`` URL only.
    * Locally we print ``http://127.0.0.1:<port>`` plus the LAN IP URL
      if one was detected, plus troubleshooting hints.
    """
    WIDTH = 66

    def pad(text: str) -> str:
        return "|  " + text.ljust(WIDTH - 4) + " |"

    lines = [
        "",
        "+" + "-" * WIDTH + "+",
        pad("Zelretch Deployment Wizard"),
        pad(""),
    ]

    if _is_huggingface_space():
        space_url = _hf_space_url() or f"http://0.0.0.0:{port}"
        lines.extend([
            pad("Hugging Face Space detected."),
            pad(""),
            pad("Open this URL in your browser:"),
            pad(""),
            pad(f"  {space_url}"),
            pad(""),
            pad("(If you see a 'running' badge in the HF UI but the URL"),
            pad("doesn't load, wait 30s for the build to finish, then"),
            pad("refresh. The wizard listens on port 7860.)"),
            pad(""),
            pad("Tip: set DATABASE_URL as a Space secret so the wizard"),
            pad("can auto-restore your saved configuration on every"),
            pad("container restart and auto-deploy the bot automatically."),
        ])
    else:
        local_url = f"http://127.0.0.1:{port}"
        lan_ip = _detect_lan_ip()
        lan_url = f"http://{lan_ip}:{port}" if lan_ip else None

        lines.extend([
            pad("Open ONE of these URLs in your browser:"),
            pad(""),
            pad(f"  1) {local_url}   <- try this first"),
        ])
        if lan_url and lan_ip not in ("127.0.0.1", "0.0.0.0"):
            lines.append(pad(f"  2) {lan_url}"))
            lines.append(pad("      (use this from another device, or if #1 fails)"))
        lines.extend([
            pad(""),
            pad("If neither URL loads:"),
            pad("  - Verify the wizard is still running in this terminal."),
            pad("  - Docker users: confirm ports: \"8765:8765\" is in your"),
            pad("    docker-compose.yml, and that you ran `docker compose up`"),
            pad("    (not just `docker build`)."),
            pad("  - Test reachability by visiting:"),
            pad(f"      {local_url}/api/ping"),
            pad("    (should return JSON like {\"ok\": true, ...})."),
        ])

    lines.extend([
        pad(""),
        pad("Press Ctrl+C to stop the wizard and abort deployment."),
    ])
    lines.append("+" + "-" * WIDTH + "+")
    print("\n".join(lines))


# ---------------------------------------------------------------------------
# Auto-restore on startup
# ---------------------------------------------------------------------------

def _try_auto_restore() -> dict | None:
    """If ``DATABASE_URL`` is set in the environment, try to fetch a
    saved configuration from MongoDB. Returns the config dict, or
    ``None`` if no DATABASE_URL is set / no saved config exists / the
    DB is unreachable.

    This makes Hugging Face Spaces re-deploys painless: set
    ``DATABASE_URL`` as a Space secret once, and every subsequent
    container restart will auto-load the saved config so the user
    only has to click *Deploy*.
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return None
    db_name = os.environ.get("DATABASE_NAME", "Zelretch")

    print(f"DATABASE_URL detected — attempting auto-restore from '{db_name}'...")
    try:
        from deploy.storage import fetch_saved_config
        ok, config, msg = asyncio.run(fetch_saved_config(db_url, db_name))
        if not ok:
            print(f"  Auto-restore failed: {msg}")
            return None
        if not config:
            print("  No saved configuration found in this database.")
            return None
        print("  Saved configuration restored. The review page is pre-filled.")
        return config
    except Exception as exc:  # noqa: BLE001
        print(f"  Auto-restore error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    os.chdir(_PROJECT_ROOT)
    # sys.path was already set up at module top-level (before any imports
    # that need the kurigram shim), but ensure it again here in case
    # main() is called from a different working directory.
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))

    _ensure_deps()

    from deploy.server import create_app

    host, port = _resolve_host_and_port()
    _print_banner(host, port)

    # Auto-restore if DATABASE_URL is set as an env var (e.g. HF secret).
    restored_config = _try_auto_restore()

    # If we're on Hugging Face AND the restored config has all required
    # variables, auto-deploy the bot immediately without waiting for the
    # user to visit the wizard URL. This makes HF Space restarts fully
    # automatic — the bot comes back online on its own.
    should_auto_deploy = False
    if restored_config and _is_huggingface_space():
        required = ["API_HASH", "API_ID", "BOT_TOKEN",
                    "DATABASE_URL", "LOGGER_ID", "OWNER_ID"]
        if all(restored_config.get(k) for k in required):
            should_auto_deploy = True
            print("All required variables found in saved config.")
            print("Auto-deploy enabled — the bot will start automatically.")
        else:
            missing = [k for k in required if not restored_config.get(k)]
            print(f"Auto-deploy skipped — missing variables: {', '.join(missing)}")
            print("Visit the wizard URL to complete deployment manually.")

    app = create_app(initial_config=restored_config,
                     auto_deploy=should_auto_deploy)

    # Only auto-open a browser when running locally. Inside HF Spaces
    # there is no GUI, and the user opens the hf.space URL instead.
    if not _is_huggingface_space():
        open_url = f"http://127.0.0.1:{port}"

        def open_browser() -> None:
            import time
            time.sleep(1.0)
            try:
                webbrowser.open(open_url)
            except Exception:
                pass

        threading.Thread(target=open_browser, daemon=True).start()

    try:
        app.run(host=host, port=port, debug=False, use_reloader=False,
                threaded=True)
    except KeyboardInterrupt:
        print("\nWizard stopped by user.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

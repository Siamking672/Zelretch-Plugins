"""
Self-updater — pulls latest from the plugin repo at startup.

Combines:
- Zelretch's ``initialize_git()`` (git-based plugin repo sync)
- FoxUserbot's ``update`` / ``beta`` commands (download zip, overlay, restart)

The updater operates on the *external plugins* directory, NOT the main
project. Main project updates are left to the user / deployment platform
(Heroku auto-deploys, Docker rebuild, systemd git-pull, etc.).
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from astralbot.helpers.net import fetch_text  # noqa: F401  (kept for parity)

if TYPE_CHECKING:
    from astralbot.core.config import Config

LOGS = logging.getLogger("astralbot.updater")


async def clone_or_pull_plugin_repo(config: "Config") -> Path | None:
    """Ensure the external plugin repo is present and up-to-date.

    Returns the path to the plugin directory, or None on failure.
    """
    target = config.data_dir / "external_plugins"
    target.mkdir(parents=True, exist_ok=True)

    # We always re-download the zip — simpler than maintaining a git checkout
    # and avoids requiring git to be installed.
    repo = config.plugin_repo
    branch = config.plugin_branch
    zip_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"

    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(zip_url) as resp:
                if resp.status != 200:
                    LOGS.warning("Plugin repo fetch failed: HTTP %s", resp.status)
                    return None
                data = await resp.read()
    except Exception as exc:
        LOGS.warning("Plugin repo fetch failed: %s", exc)
        # Fall back to existing checkout if we have one
        existing = target / config.plugin_path
        if existing.exists():
            LOGS.info("Using cached external plugins at %s", existing)
            return existing
        return None

    zip_path = target / "plugins.zip"
    zip_path.write_bytes(data)

    # Clear previous extract
    for child in target.iterdir():
        if child.is_dir() and child.name != config.plugin_path:
            shutil.rmtree(child, ignore_errors=True)

    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target)
    except Exception as exc:
        LOGS.warning("Plugin zip extract failed: %s", exc)
        return None

    # The zip extracts to <repo>-<branch>/... — find it and move
    extracted = [
        c for c in target.iterdir()
        if c.is_dir() and c.name != config.plugin_path
    ]
    if not extracted:
        return None
    src_root = extracted[0]
    plugin_src = src_root / config.plugin_path
    if not plugin_src.exists():
        # Repo might not have a "modules/" dir — use the root
        plugin_src = src_root

    plugin_dest = target / config.plugin_path
    if plugin_dest.exists():
        shutil.rmtree(plugin_dest)
    shutil.move(str(plugin_src), str(plugin_dest))
    shutil.rmtree(src_root, ignore_errors=True)
    zip_path.unlink(missing_ok=True)

    LOGS.info("External plugins updated from %s@%s → %s", repo, branch, plugin_dest)
    return plugin_dest


def restart_process(*extra_args: str) -> None:
    """Restart the current Python process. Used by .restart builtin."""
    import sys
    os.execv(sys.executable, [sys.executable] + sys.argv + list(extra_args))

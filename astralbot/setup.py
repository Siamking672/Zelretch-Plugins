"""Standalone entry point for the setup wizard.

Run with::

    python -m astralbot.setup

This always launches the wizard, regardless of whether .env exists.
Useful for re-configuring an existing install.
"""

from __future__ import annotations

import sys

from astralbot.setup_wizard import run_wizard, get_persistent_env_path


def main() -> int:
    return run_wizard(env_path=get_persistent_env_path(), auto_open=None)


if __name__ == "__main__":
    sys.exit(main())

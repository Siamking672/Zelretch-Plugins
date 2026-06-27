#!/usr/bin/env bash
#
# AstralBot installer for VPS (systemd) deployments.
# Run as root (or with sudo). Idempotent — safe to re-run.
#
# This script installs the code and dependencies but does NOT start the bot.
# After running it, edit .env (or run the setup wizard) and then:
#
#   systemctl start astralbot
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/AstralBot/AstralBot/main/install.sh | bash
#   — or —
#   bash install.sh
#
set -euo pipefail

INSTALL_DIR="/opt/astralbot"
SERVICE_NAME="astralbot"
SERVICE_USER="astralbot"
PYTHON_BIN="${PYTHON_BIN:-python3}"

err()   { echo "[ERROR] $*" >&2; exit 1; }
info()  { echo "[INFO] $*"; }
warn()  { echo "[WARN] $*"; }

# --- Pre-flight checks ------------------------------------------------------

if [[ $EUID -ne 0 ]]; then
    err "This script must be run as root (use sudo)."
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    err "Python 3 not found. Install Python 3.11+ first: apt install python3 python3-venv python3-pip"
fi

PY_VERSION=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Detected Python $PY_VERSION"

# --- Create user ------------------------------------------------------------

if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
    info "Creating system user '$SERVICE_USER'"
    useradd --system --create-home --home-dir "$INSTALL_DIR" --shell /bin/bash "$SERVICE_USER"
else
    info "User '$SERVICE_USER' already exists"
fi

# --- Clone / update source --------------------------------------------------

if [[ ! -d "$INSTALL_DIR/astralbot" ]]; then
    info "Cloning AstralBot into $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    chown "$SERVICE_USER":"$SERVICE_USER" "$INSTALL_DIR"
    sudo -u "$SERVICE_USER" git clone https://github.com/AstralBot/AstralBot.git "$INSTALL_DIR"
else
    info "Source already present at $INSTALL_DIR — pulling latest"
    sudo -u "$SERVICE_USER" git -C "$INSTALL_DIR" pull --ff-only
fi

cd "$INSTALL_DIR"

# --- Virtualenv + deps ------------------------------------------------------

if [[ ! -d "venv" ]]; then
    info "Creating virtualenv"
    sudo -u "$SERVICE_USER" "$PYTHON_BIN" -m venv venv
fi

info "Installing Python dependencies"
sudo -u "$SERVICE_USER" venv/bin/pip install --upgrade pip wheel
sudo -u "$SERVICE_USER" venv/bin/pip install -r requirements.txt

# --- Data directories -------------------------------------------------------

for d in userdata/plugins userdata/downloads userdata/temp userdata/external_plugins logs; do
    mkdir -p "$INSTALL_DIR/$d"
    chown -R "$SERVICE_USER":"$SERVICE_USER" "$INSTALL_DIR/$d"
done

# --- systemd service --------------------------------------------------------

info "Installing systemd unit"
cp astralbot.service /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# --- Done -------------------------------------------------------------------

cat <<EOF

✅ AstralBot installed to $INSTALL_DIR

Next steps — choose ONE of these two setup paths:

  ╔═══════════════════════════════════════════════════════════════════╗
  ║  PATH A: Interactive setup wizard (recommended)                   ║
  ╚═══════════════════════════════════════════════════════════════════╝

    1. Run the wizard (as the astralbot user):
         sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/python -m astralbot

       A web page opens at http://localhost:8080 — fill in your API
       credentials, optionally create a session, then click Deploy.

    2. Once the wizard writes .env and exits, start the service:
         systemctl start $SERVICE_NAME

  ╔═══════════════════════════════════════════════════════════════════╗
  ║  PATH B: Manual .env file                                          ║
  ╚═══════════════════════════════════════════════════════════════════╝

    1. Create the .env file:
         sudo -u $SERVICE_USER nano $INSTALL_DIR/.env

       At minimum:
         API_ID=...
         API_HASH=...
         STRING_SESSION=...    # generate with: venv/bin/python -m astralbot.utils.gen_session

    2. Start the service:
         systemctl start $SERVICE_NAME

  Common commands:
    systemctl status $SERVICE_NAME
    journalctl -u $SERVICE_NAME -f
    systemctl restart $SERVICE_NAME
    systemctl stop $SERVICE_NAME

  To re-run the setup wizard later:
    sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/python -m astralbot.setup

  To update later (re-run this script):
    bash install.sh

EOF

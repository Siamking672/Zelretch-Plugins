"""
AstralBot Setup Wizard — a Flask-based interactive setup flow.

Run with::

    python -m astralbot            # auto-launches if .env is missing
    python -m astralbot.setup      # explicit launch
    python -m astralbot --setup    # force-launch even if .env exists

The wizard has three pages:

  Page 1 — Required + optional config vars (API_ID, API_HASH, etc.)
  Page 2 — Userbot session creation (interactive phone → code → 2FA).
           SKIPPABLE — the user can paste an existing session string,
           skip entirely, or come back later via the `.session` bot command.
  Page 3 — Review collected config + Deploy button.

Deployment modes
----------------

The wizard auto-detects its deployment environment via the SPACE_ID env var
(set by HuggingFace Spaces on every Space):

  LOCAL (no SPACE_ID):
    - Binds Flask to 127.0.0.1:8080
    - Auto-opens the user's browser
    - On Deploy: writes .env to ./, starts the bot as a detached subprocess,
      wizard process exits. The bot inherits stdout/stderr.

  HUGGINGFACE SPACES (SPACE_ID is set):
    - Binds Flask to 0.0.0.0:$PORT (default 7860) — required by HF's reverse proxy
    - Does NOT auto-open a browser (the user accesses via the HF Space URL)
    - On Deploy: writes .env to /data/.env (persistent storage if enabled),
      starts the bot in a background asyncio thread within the same process
      so Flask keeps serving HTTP. HF Spaces requires the container to keep
      serving HTTP or it gets marked as failed.
    - Adds /health endpoint for HF Spaces liveness probes.
    - Adds /status page showing bot running state.

Inspired by FoxUserbot's web_auth flow, but with a cleaner multi-step UX,
the ability to defer session creation, and proper HF Spaces support.
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------


def is_hf_space() -> bool:
    """True if running inside a HuggingFace Spaces Docker container.

    HF Spaces sets the SPACE_ID env var on every Space (format: 'username/space-name').
    """
    return bool(os.environ.get("SPACE_ID"))


def get_bind_host() -> str:
    """Return the host Flask should bind to."""
    if is_hf_space():
        return "0.0.0.0"
    return "127.0.0.1"


def get_bind_port(default: int = 8080) -> int:
    """Return the port Flask should bind to.

    On HF Spaces: prefers $PORT (HF sets this to 7860 by default).
    Locally: prefers 8080.
    """
    if is_hf_space():
        return int(os.environ.get("PORT", "7860"))
    return int(os.environ.get("PORT", str(default)))


def get_persistent_env_path() -> Path:
    """Return the path to use for .env.

    On HF Spaces with persistent storage enabled, /data is mounted as a
    persistent volume — we write there so config survives container restarts.
    Otherwise, fall back to ./userdata/.env (which on HF Spaces without
    persistent storage will be ephemeral — the user would need to re-run
    the wizard on each container restart, OR set the config via HF Secrets).
    """
    if is_hf_space():
        # Try /data first (HF persistent storage)
        data_dir = Path("/data")
        if data_dir.exists() and os.access(data_dir, os.W_OK):
            return data_dir / ".env"
        # Fall back to ./userdata/.env
        return Path("userdata") / ".env"
    return Path(".env")


# ---------------------------------------------------------------------------
# Wizard state
# ---------------------------------------------------------------------------

# Wizard state — persists across Flask requests within a single wizard run.
# We don't need session cookies because the wizard runs single-user on
# localhost for a few minutes.
_STATE: dict[str, Any] = {
    "vars": {},                # collected env vars (API_ID, API_HASH, etc.)
    "session_string": None,    # final session string (if user created/pasted one)
    "phone": None,
    "code_hash": None,
    "phone_code_hash": None,
    "pyrogram_client": None,   # long-lived Client during the code → sign_in flow
    "2fa_needed": False,
    "error": None,
    "info": None,
    "deployed": False,         # set True after Deploy click
    "bot_status": "not_started",  # not_started | starting | running | failed
    "bot_error": None,         # last error from bot startup (if any)
    "bot_pid": None,           # subprocess PID (local mode)
    "bot_thread": None,        # background thread (HF Spaces mode)
}

# A dedicated asyncio loop running in a background thread — pyrogram's async
# Client must be operated from the same loop across requests.
_wizard_loop: asyncio.AbstractEventLoop | None = None
_wizard_thread: threading.Thread | None = None


def _start_wizard_loop() -> None:
    global _wizard_loop, _wizard_thread
    if _wizard_loop is not None:
        return
    _wizard_loop = asyncio.new_event_loop()
    _wizard_thread = threading.Thread(target=_wizard_loop.run_forever, daemon=True)
    _wizard_thread.start()


def _run_async(coro, timeout: int = 120):
    """Run a coroutine in the wizard's background loop, blocking until done."""
    _start_wizard_loop()
    assert _wizard_loop is not None
    future = asyncio.run_coroutine_threadsafe(coro, _wizard_loop)
    return future.result(timeout=timeout)


# ---------------------------------------------------------------------------
# HTML pages
# ---------------------------------------------------------------------------

_BASE_CSS = """
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    margin: 0;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .card {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    max-width: 640px;
    width: 100%;
    padding: 40px;
  }
  h1 { color: #2c3e50; margin-top: 0; font-size: 28px; }
  h2 { color: #555; font-size: 18px; margin-top: 24px; }
  .step-indicator {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
  }
  .step {
    flex: 1;
    height: 4px;
    background: #e0e0e0;
    border-radius: 2px;
  }
  .step.active { background: #667eea; }
  .step.done { background: #52c41a; }
  label {
    display: block;
    color: #333;
    font-weight: 500;
    margin: 16px 0 6px;
    font-size: 14px;
  }
  .hint { color: #888; font-size: 12px; margin-top: 4px; }
  input[type=text], input[type=password], input[type=number] {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    font-size: 14px;
    font-family: monospace;
  }
  input:focus { outline: none; border-color: #667eea; }
  .required { color: #e74c3c; }
  button, .btn {
    background: #667eea;
    color: #fff;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    margin-top: 20px;
  }
  button:hover, .btn:hover { background: #5568d3; }
  button.secondary, .btn.secondary {
    background: #f0f0f0;
    color: #333;
  }
  button.secondary:hover, .btn.secondary:hover { background: #e0e0e0; }
  button.deploy {
    background: linear-gradient(135deg, #52c41a 0%, #38a169 100%);
    font-size: 18px;
    padding: 16px 48px;
    width: 100%;
  }
  .alert {
    padding: 12px 16px;
    border-radius: 6px;
    margin: 16px 0;
    font-size: 14px;
  }
  .alert.error { background: #fee; color: #c33; border: 1px solid #fcc; }
  .alert.info { background: #e6f7ff; color: #0066cc; border: 1px solid #91d5ff; }
  .alert.success { background: #f6ffed; color: #389e0d; border: 1px solid #b7eb8f; }
  .row { display: flex; gap: 12px; }
  .row > * { flex: 1; }
  .summary {
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 16px;
    font-family: monospace;
    font-size: 13px;
    line-height: 1.6;
  }
  .summary .key { color: #667eea; }
  .summary .val { color: #333; }
  .summary .redacted { color: #999; }
  code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
</style>
"""


def _page_wrapper(title: str, step: int, body: str) -> str:
    """Wrap page body with the standard layout. step: 1, 2, or 3."""
    steps = [""] * 3
    for i in range(3):
        if i + 1 < step:
            steps[i] = "done"
        elif i + 1 == step:
            steps[i] = "active"
    step_html = '<div class="step-indicator">' + "".join(
        f'<div class="step {s}"></div>' for s in steps
    ) + '</div>'
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — AstralBot Setup</title>
  {_BASE_CSS}
</head>
<body>
  <div class="card">
    <h1>✨ AstralBot Setup</h1>
    {step_html}
    {body}
  </div>
</body>
</html>"""


PAGE1_BODY = """
<form method="post" action="/">
<h2>Step 1 — Telegram API credentials</h2>
<p style="color:#666;font-size:14px;">
  Get your <code>API_ID</code> and <code>API_HASH</code> from
  <a href="https://my.telegram.org/apps" target="_blank">my.telegram.org/apps</a>.
  Create an app there (any name works) and copy the values here.
</p>

<label>API_ID <span class="required">*</span></label>
<input type="number" name="api_id" placeholder="12345678" required>

<label>API_HASH <span class="required">*</span></label>
<input type="text" name="api_hash" placeholder="0123456789abcdef0123456789abcdef" required>

<h2>Optional — assistant bot</h2>
<p style="color:#666;font-size:14px;">
  If you want an assistant bot (for inline help, PM management), create one
  via <a href="https://t.me/BotFather" target="_blank">@BotFather</a> and
  paste the token here. You can skip this and add it later via
  <code>.setvar BOT_TOKEN ...</code>.
</p>
<label>BOT_TOKEN (optional)</label>
<input type="text" name="bot_token" placeholder="123456:ABC-DEF1234ghijk...">

<h2>Optional — advanced</h2>
<p style="color:#666;font-size:14px;">
  Leave these at defaults unless you know what you're doing.
</p>

<label>Command prefixes</label>
<input type="text" name="handlers" value=". !" placeholder=". !">
<div class="hint">Space-separated list of trigger characters.</div>

<label>Database URL (optional)</label>
<input type="text" name="database_url" placeholder="mongodb+srv://... (leave blank for SQLite)">
<div class="hint">If blank, AstralBot uses SQLite (zero-config, file-based).</div>

<label>Log chat ID (optional — leave blank)</label>
<input type="text" name="log_chat_id" placeholder="-1001234567890">
<div class="hint">
  The ID of an <strong>existing</strong> Telegram channel/group where the bot
  can forward WARNING+ logs. The bot must already be a member (add it as admin).
  <strong>Leave blank</strong> if you don't have one — logs will only go to the
  log file and console. You can set this later via <code>.setvar LOG_CHAT_ID ...</code>.
</div>

<label>Plugin repo (optional)</label>
<input type="text" name="plugin_repo" value="AstralBot/AstralModules">
<div class="hint">External plugin repository (GitHub owner/repo).</div>

<div style="display:flex;gap:12px;margin-top:24px;">
  <button type="submit" style="flex:1;">Next →</button>
</div>
</form>
"""


PAGE2_BODY_TEMPLATE = """
<form method="post" action="/session">
<h2>Step 2 — Userbot session</h2>
<p style="color:#666;font-size:14px;">
  AstralBot runs on your personal Telegram account. To do that it needs a
  <em>session string</em> — a long secret that lets it log in as you.
  You have three options:
</p>

<div style="margin: 20px 0; padding: 16px; background: #f8f9fa; border-radius: 6px;">
  <strong>Option A:</strong> Create a new session interactively below.<br>
  <strong>Option B:</strong> Paste an existing session string.<br>
  <strong>Option C:</strong> Skip — do it later from inside the bot via <code>.session</code>.
</div>

{info_block}
{error_block}

{step_block}

<hr style="margin: 32px 0; border: none; border-top: 1px solid #e0e0e0;">

<h2>Option B — Paste existing session</h2>
<label>Session string</label>
<input type="text" name="session_string" placeholder="BQAB...very long string..." style="font-size: 11px;">
<button type="submit" name="action" value="paste_session" class="secondary">Use this session</button>

<hr style="margin: 32px 0; border: none; border-top: 1px solid #e0e0e0;">

<h2>Option C — Skip</h2>
<p style="color:#666;font-size:14px;">
  You can create the session later. After the bot starts, DM it
  <code>.session</code> to launch the in-bot session creator.
  <strong>Note:</strong> if you didn't provide a BOT_TOKEN in step 1,
  the bot cannot start until you create a session here.
</p>
<button type="submit" name="action" value="skip" class="secondary">Skip →</button>
</form>
"""


PAGE3_BODY_TEMPLATE = """
<h2>Step 3 — Review and deploy</h2>
<p style="color:#666;font-size:14px;">
  Review the configuration below. Click <strong>Deploy</strong> to write
  <code>.env</code> and start AstralBot.
</p>

{warning_block}

<h2>Configuration</h2>
<div class="summary">
{summary_html}
</div>

<form method="post" action="/deploy">
  <button type="submit" class="deploy">🚀 Deploy AstralBot</button>
</form>

<p style="color:#999;font-size:12px;margin-top:16px;">
  After deploy, this wizard process will exit and the bot will start in the
  background. Check the terminal for log output.
</p>
"""


SUCCESS_BODY = """
<h2>✅ Deployed!</h2>
<div class="alert success">
  AstralBot is starting up. Check the terminal where you ran the wizard
  for log output.
</div>

<p style="color:#666;font-size:14px;">
  The wizard process will exit in <span id="countdown">3</span> seconds.
  You can close this tab.
</p>

<script>
  let n = 3;
  setInterval(() => {
    n--;
    document.getElementById('countdown').textContent = n;
    if (n <= 0) window.close();
  }, 1000);
</script>
"""


SUCCESS_BODY_HF = """
<h2>✅ Deploying...</h2>
<div class="alert success">
  AstralBot is starting in the background. This page will refresh in
  <span id="countdown">5</span> seconds to show the bot status.
</div>

<p style="color:#666;font-size:14px;">
  The wizard stays running so the HuggingFace Space keeps responding to
  health checks. You can check the bot status anytime at
  <a href="/status">/status</a> or <a href="/health">/health</a>.
</p>

<script>
  let n = 5;
  setInterval(() => {
    n--;
    document.getElementById('countdown').textContent = n;
    if (n <= 0) window.location.href = '/status';
  }, 1000);
</script>
"""


# ---------------------------------------------------------------------------
# Pyrogram session-creation helpers (run in the background loop)
# ---------------------------------------------------------------------------


async def _send_code(api_id: int, api_hash: str, phone: str) -> dict:
    """Send a Telegram login code to the given phone. Returns dict with status."""
    from pyrogram import Client
    from pyrogram.errors import PhoneNumberInvalid, FloodWait

    # Tear down any previous client
    if _STATE["pyrogram_client"] is not None:
        try:
            await _STATE["pyrogram_client"].disconnect()
        except Exception:
            pass
        _STATE["pyrogram_client"] = None

    try:
        client = Client(
            name="astralbot_wizard",
            api_id=api_id,
            api_hash=api_hash,
            in_memory=True,
        )
        await client.connect()
        sent = await client.send_code(phone)
        _STATE["pyrogram_client"] = client
        _STATE["phone"] = phone
        _STATE["phone_code_hash"] = sent.phone_code_hash
        return {"ok": True}
    except PhoneNumberInvalid as exc:
        return {"ok": False, "error": f"Invalid phone number: {exc}"}
    except FloodWait as exc:
        return {"ok": False, "error": f"Telegram asked to wait {exc.value}s. Try again later."}
    except Exception as exc:
        return {"ok": False, "error": f"Failed to send code: {exc}"}


async def _sign_in(code: str) -> dict:
    """Sign in with the code. Returns dict indicating success / 2FA / error."""
    from pyrogram import Client
    from pyrogram.errors import (
        PhoneCodeInvalid,
        PhoneCodeExpired,
        PhoneCodeEmpty,
        SessionPasswordNeeded,
        FloodWait,
    )

    client = _STATE.get("pyrogram_client")
    if client is None:
        return {"ok": False, "error": "No active code request. Click 'Send login code' first."}

    phone = _STATE.get("phone")
    code_hash = _STATE.get("phone_code_hash")
    if not phone or not code_hash:
        return {"ok": False, "error": "State lost — start over."}

    try:
        await client.sign_in(phone, code_hash, code)
        # Success — no 2FA
        session_string = await client.export_session_string()
        _STATE["session_string"] = session_string
        await client.disconnect()
        _STATE["pyrogram_client"] = None
        return {"ok": True, "2fa": False}
    except SessionPasswordNeeded:
        _STATE["2fa_needed"] = True
        return {"ok": True, "2fa": True}
    except (PhoneCodeInvalid, PhoneCodeExpired, PhoneCodeEmpty) as exc:
        return {"ok": False, "error": f"Code error: {exc}"}
    except FloodWait as exc:
        return {"ok": False, "error": f"Telegram asked to wait {exc.value}s."}
    except Exception as exc:
        return {"ok": False, "error": f"Sign-in failed: {exc}"}


async def _check_password(password: str) -> dict:
    """Submit 2FA password."""
    from pyrogram.errors import PasswordHashInvalid, FloodWait

    client = _STATE.get("pyrogram_client")
    if client is None:
        return {"ok": False, "error": "No active session. Start over."}

    try:
        await client.check_password(password)
        session_string = await client.export_session_string()
        _STATE["session_string"] = session_string
        await client.disconnect()
        _STATE["pyrogram_client"] = None
        _STATE["2fa_needed"] = False
        return {"ok": True}
    except PasswordHashInvalid:
        return {"ok": False, "error": "Wrong password. Try again."}
    except FloodWait as exc:
        return {"ok": False, "error": f"Telegram asked to wait {exc.value}s."}
    except Exception as exc:
        return {"ok": False, "error": f"2FA failed: {exc}"}


# ---------------------------------------------------------------------------
# .env writing + bot startup
# ---------------------------------------------------------------------------


def write_env_file(state: dict, env_path: Path | str = ".env") -> Path:
    """Write the collected wizard state to a .env file. Returns the path."""
    env_path = Path(env_path)
    env_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = ["# AstralBot configuration — generated by the setup wizard."]

    vars_dict = state.get("vars", {})
    # Required
    if vars_dict.get("API_ID"):
        lines.append(f"API_ID={vars_dict['API_ID']}")
    if vars_dict.get("API_HASH"):
        lines.append(f"API_HASH={vars_dict['API_HASH']}")

    # Session / bot token
    if state.get("session_string"):
        lines.append(f"STRING_SESSION={state['session_string']}")
    if vars_dict.get("BOT_TOKEN"):
        lines.append(f"BOT_TOKEN={vars_dict['BOT_TOKEN']}")

    # Optional
    if vars_dict.get("DATABASE_URL"):
        lines.append(f"DATABASE_URL={vars_dict['DATABASE_URL']}")
    if vars_dict.get("LOG_CHAT_ID"):
        lines.append(f"LOG_CHAT_ID={vars_dict['LOG_CHAT_ID']}")
    if vars_dict.get("HANDLERS") and vars_dict["HANDLERS"] != ". !":
        lines.append(f"HANDLERS={vars_dict['HANDLERS']}")
    if vars_dict.get("PLUGIN_REPO") and vars_dict["PLUGIN_REPO"] != "AstralBot/AstralModules":
        lines.append(f"PLUGIN_REPO={vars_dict['PLUGIN_REPO']}")
    lines.append(f"PLUGIN_BRANCH=main")

    content = "\n".join(lines) + "\n"
    env_path.write_text(content, encoding="utf-8")
    return env_path


def start_bot_subprocess(env_path: Path | str = ".env") -> subprocess.Popen:
    """Start `python -m astralbot --no-wizard` in a detached subprocess.

    Used in LOCAL mode. The bot inherits the wizard's stdout/stderr so the
    user can see logs.
    """
    env_path = Path(env_path).resolve()
    # Use the same Python interpreter
    py = sys.executable
    # Start in a new process group so the wizard can exit without killing the bot
    proc = subprocess.Popen(
        [py, "-m", "astralbot", "--no-wizard"],
        env={**os.environ, "DOTENV_PATH": str(env_path)},
        stdout=None,
        stderr=None,
        start_new_session=True,
    )
    return proc


def start_bot_in_thread(env_path: Path | str = ".env") -> threading.Thread:
    """Start the bot in a background thread within the same process.

    Used in HUGGINGFACE SPACES mode — HF Spaces requires the container to
    keep serving HTTP, so we cannot fork a subprocess and exit. Instead we
    run the bot's asyncio event loop in a daemon thread; the Flask main
    thread keeps serving the wizard pages.
    """
    env_path = Path(env_path).resolve()

    def _bot_runner():
        # Set DOTENV_PATH so Config.from_env picks up our .env file
        os.environ["DOTENV_PATH"] = str(env_path)
        # Also load .env into os.environ immediately so config.from_env sees it
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, override=True)
        except ImportError:
            # Manually parse .env
            if env_path.exists():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    os.environ[key.strip()] = val.strip()  # override

        # IMPORTANT: Pyrogram's async_to_sync wrapper calls asyncio.get_event_loop()
        # at module-import time, which fails in a thread without an event loop.
        # We must create and set the event loop BEFORE importing pyrogram (which
        # happens transitively when we import astralbot.__main__).
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        _STATE["bot_status"] = "starting"
        try:
            # Import the bot's main() function. This triggers pyrogram import
            # which needs the event loop set (done above).
            import astralbot.__main__ as bot_main_module
            bot_main = bot_main_module.main
            _STATE["bot_status"] = "running"
            try:
                exit_code = loop.run_until_complete(bot_main())
                # bot_main() returns 0 on clean shutdown, non-zero on failure
                if exit_code and exit_code != 0:
                    _STATE["bot_status"] = "failed"
                    _STATE["bot_error"] = f"Bot exited with code {exit_code} (check logs for details)"
                else:
                    # Clean shutdown — bot stopped without error
                    _STATE["bot_status"] = "stopped"
            except KeyboardInterrupt:
                _STATE["bot_status"] = "stopped"
            except SystemExit as se:
                # SystemExit can be raised by sys.exit() inside the bot
                if se.code and str(se.code) != "0":
                    _STATE["bot_status"] = "failed"
                    _STATE["bot_error"] = f"Bot exited with code {se.code}"
                else:
                    _STATE["bot_status"] = "stopped"
            except Exception as exc:
                _STATE["bot_status"] = "failed"
                _STATE["bot_error"] = f"{type(exc).__name__}: {exc}"
                import traceback
                traceback.print_exc()
        except Exception as exc:
            _STATE["bot_status"] = "failed"
            _STATE["bot_error"] = f"{type(exc).__name__}: {exc}"
            import traceback
            traceback.print_exc()

    t = threading.Thread(target=_bot_runner, daemon=True, name="astralbot-bot")
    t.start()
    return t


def deploy(env_path: Path | str = ".env") -> None:
    """Deploy the bot. Picks the right strategy based on environment.

    LOCAL: start a subprocess (wizard process will exit after).
    HF SPACES: start a background thread (wizard keeps serving HTTP).
    """
    env_path = Path(env_path).resolve()
    if is_hf_space():
        _STATE["bot_thread"] = start_bot_in_thread(env_path)
    else:
        proc = start_bot_subprocess(env_path)
        _STATE["bot_pid"] = proc.pid
    _STATE["deployed"] = True


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------


def make_app(env_path: Path | str = ".env") -> "Flask":
    """Build the Flask app for the wizard."""
    from flask import Flask, request, redirect

    env_path = Path(env_path)
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def page1():
        if request.method == "POST":
            api_id = request.form.get("api_id", "").strip()
            api_hash = request.form.get("api_hash", "").strip()
            if not api_id or not api_hash:
                body = '<div class="alert error">API_ID and API_HASH are required.</div>' + PAGE1_BODY
                return _page_wrapper("Step 1", 1, body), 400
            try:
                int(api_id)
            except ValueError:
                body = '<div class="alert error">API_ID must be an integer.</div>' + PAGE1_BODY
                return _page_wrapper("Step 1", 1, body), 400

            _STATE["vars"] = {
                "API_ID": api_id,
                "API_HASH": api_hash,
                "BOT_TOKEN": request.form.get("bot_token", "").strip(),
                "HANDLERS": request.form.get("handlers", ". !").strip() or ". !",
                "DATABASE_URL": request.form.get("database_url", "").strip(),
                "LOG_CHAT_ID": request.form.get("log_chat_id", "").strip(),
                "PLUGIN_REPO": request.form.get("plugin_repo", "AstralBot/AstralModules").strip() or "AstralBot/AstralModules",
            }
            _STATE["error"] = None
            _STATE["info"] = None
            return redirect("/session")

        # GET — clear state for a fresh start
        _STATE["error"] = None
        _STATE["info"] = None
        _STATE["2fa_needed"] = False
        return _page_wrapper("Step 1", 1, PAGE1_BODY)

    @app.route("/session", methods=["GET", "POST"])
    def page2():
        if not _STATE.get("vars"):
            return redirect("/")

        if request.method == "POST":
            action = request.form.get("action", "")

            if action == "skip":
                _STATE["error"] = None
                _STATE["info"] = None
                return redirect("/deploy")

            elif action == "paste_session":
                sess = request.form.get("session_string", "").strip()
                if not sess:
                    _STATE["error"] = "No session string provided."
                else:
                    _STATE["session_string"] = sess
                    _STATE["error"] = None
                    _STATE["info"] = "Session string saved."
                    return redirect("/deploy")
                return _render_page2()

            elif action == "request_code":
                phone = request.form.get("phone", "").strip()
                if not phone:
                    _STATE["error"] = "Please enter your phone number."
                    return _render_page2()
                api_id = int(_STATE["vars"]["API_ID"])
                api_hash = _STATE["vars"]["API_HASH"]
                result = _run_async(_send_code(api_id, api_hash, phone))
                if result.get("ok"):
                    _STATE["error"] = None
                    _STATE["info"] = f"Login code sent to {phone}. Check Telegram."
                else:
                    _STATE["error"] = result.get("error", "Unknown error.")
                    _STATE["info"] = None
                return _render_page2()

            elif action == "submit_code":
                code = request.form.get("code", "").strip()
                if not code:
                    _STATE["error"] = "Please enter the code you received."
                    return _render_page2()
                result = _run_async(_sign_in(code))
                if result.get("ok"):
                    if result.get("2fa"):
                        _STATE["error"] = None
                        _STATE["info"] = "Two-factor authentication required. Enter your password below."
                    else:
                        _STATE["error"] = None
                        _STATE["info"] = "✅ Session created successfully!"
                        return redirect("/deploy")
                else:
                    _STATE["error"] = result.get("error", "Sign-in failed.")
                return _render_page2()

            elif action == "submit_password":
                password = request.form.get("password", "").strip()
                if not password:
                    _STATE["error"] = "Please enter your 2FA password."
                    return _render_page2()
                result = _run_async(_check_password(password))
                if result.get("ok"):
                    _STATE["error"] = None
                    _STATE["info"] = "✅ Session created successfully!"
                    return redirect("/deploy")
                else:
                    _STATE["error"] = result.get("error", "2FA failed.")
                return _render_page2()

        # GET
        return _render_page2()

    @app.route("/deploy", methods=["GET", "POST"])
    def page3():
        if not _STATE.get("vars"):
            return redirect("/")

        if request.method == "POST":
            # User clicked Deploy
            env_file = write_env_file(_STATE, env_path=env_path)
            deploy(env_path=env_file)
            # Show success page (different for local vs HF Spaces)
            if is_hf_space():
                return _page_wrapper("Deployed", 3, SUCCESS_BODY_HF)
            return _page_wrapper("Deployed", 3, SUCCESS_BODY)

        # GET — show review
        return _render_page3()

    @app.route("/health")
    def health():
        """Health-check endpoint for HF Spaces liveness probes.

        Returns 200 OK once Flask is up. After Deploy, also reports bot status.
        """
        from flask import jsonify
        return jsonify({
            "status": "ok",
            "deployed": _STATE.get("deployed", False),
            "bot_status": _STATE.get("bot_status", "not_started"),
            "bot_error": _STATE.get("bot_error"),
        }), 200

    @app.route("/status")
    def status():
        """Status page (mainly for HF Spaces — shows bot running state)."""
        if not _STATE.get("deployed"):
            return redirect("/")
        bot_status = _STATE.get("bot_status", "not_started")
        bot_error = _STATE.get("bot_error")
        status_emoji = {
            "not_started": "⏳",
            "starting": "🔄",
            "running": "✅",
            "failed": "❌",
        }.get(bot_status, "❓")
        error_block = ""
        if bot_error:
            error_block = f'<div class="alert error"><strong>Error:</strong> <code>{bot_error}</code></div>'
        body = f"""
<h2>🤖 Bot Status</h2>
<div class="alert info">
  Status: {status_emoji} <strong>{bot_status}</strong>
</div>
{error_block}
<p style="color:#666;font-size:14px;">
  The bot is running in the background. Check the Space logs for detailed output.
  If you need to reconfigure, edit the secrets in your HuggingFace Space settings
  (or remove <code>/data/.env</code> to relaunch the wizard).
</p>
<p style="color:#666;font-size:14px;">
  <a href="/status">Refresh</a> · <a href="/health">JSON health</a>
</p>
"""
        return _page_wrapper("Status", 3, body)

    return app


def _render_page2() -> str:
    """Render page 2 with the sequential session-creation flow.

    The "Option A" section is a state machine that shows only ONE input field
    at a time:

      * Default (no phone yet)   → phone input
      * Phone sent, awaiting code → login code input
      * 2FA required              → password input
      * Session created           → success message (no input)

    Each field "disappears" when submitted because we re-render the page with
    only the next step's field visible.
    """
    info_block = ""
    if _STATE.get("info"):
        info_block = f'<div class="alert info">{_STATE["info"]}</div>'
    error_block = ""
    if _STATE.get("error"):
        error_block = f'<div class="alert error">{_STATE["error"]}</div>'

    # Build the step block — only ONE of these will be rendered
    step_block = ""

    if _STATE.get("session_string"):
        # Session created — show success, no further input needed
        step_block = """
        <h2>Option A — Create a new session</h2>
        <div class="alert success">
          ✅ Session created successfully! Click <strong>Next</strong> below
          to continue to deployment.
        </div>
        <div style="margin-top:16px;">
          <a href="/deploy" class="btn">Next →</a>
        </div>
        """
    elif _STATE.get("2fa_needed"):
        # 2FA password step
        step_block = """
        <h2>Option A — Create a new session</h2>
        <p style="color:#666;font-size:14px;">
          🔒 Your account has two-factor authentication enabled.
          Enter your cloud password to continue.
        </p>
        <input type="hidden" name="action" value="submit_password">
        <label>2FA password</label>
        <input type="password" name="password" placeholder="Your cloud password" autofocus>
        <button type="submit" class="secondary">Submit password</button>
        """
    elif _STATE.get("phone") and _STATE.get("phone_code_hash"):
        # Login code step — phone was accepted, code was sent
        step_block = """
        <h2>Option A — Create a new session</h2>
        <p style="color:#666;font-size:14px;">
          📞 Login code sent to your phone. Enter it below to continue.
        </p>
        <input type="hidden" name="action" value="submit_code">
        <label>Login code</label>
        <input type="text" name="code" placeholder="12345" autocomplete="off" autofocus>
        <button type="submit" class="secondary">Verify code</button>
        """
    else:
        # Initial step — phone number input
        step_block = """
        <h2>Option A — Create a new session</h2>
        <p style="color:#666;font-size:14px;">
          Enter your phone number with country code. Telegram will send a
          login code to this number via SMS or the Telegram app.
        </p>
        <input type="hidden" name="action" value="request_code">
        <label>Phone number (with country code)</label>
        <input type="text" name="phone" placeholder="+15551234567" autofocus>
        <div class="hint">Example: <code>+15551234567</code></div>
        <button type="submit" class="secondary">Send login code</button>
        """

    body = PAGE2_BODY_TEMPLATE.format(
        info_block=info_block,
        error_block=error_block,
        step_block=step_block,
    )
    return _page_wrapper("Step 2", 2, body)


def _render_page3() -> str:
    """Render page 3 with the configuration summary."""
    vars_dict = _STATE.get("vars", {})
    has_session = bool(_STATE.get("session_string"))
    has_bot_token = bool(vars_dict.get("BOT_TOKEN"))

    summary_lines: list[str] = []
    summary_lines.append(f'<span class="key">API_ID</span> = <span class="val">{vars_dict.get("API_ID", "")}</span>')
    summary_lines.append(f'<span class="key">API_HASH</span> = <span class="val">{vars_dict.get("API_HASH", "")[:8]}... (redacted)</span>')
    if has_session:
        summary_lines.append(f'<span class="key">STRING_SESSION</span> = <span class="redacted">(set, {len(_STATE["session_string"])} chars)</span>')
    else:
        summary_lines.append(f'<span class="key">STRING_SESSION</span> = <span class="redacted">(not set)</span>')
    if has_bot_token:
        summary_lines.append(f'<span class="key">BOT_TOKEN</span> = <span class="redacted">(set)</span>')
    if vars_dict.get("DATABASE_URL"):
        summary_lines.append(f'<span class="key">DATABASE_URL</span> = <span class="redacted">(set)</span>')
    else:
        summary_lines.append(f'<span class="key">DATABASE_URL</span> = <span class="redacted">(not set — SQLite will be used)</span>')
    if vars_dict.get("LOG_CHAT_ID"):
        summary_lines.append(f'<span class="key">LOG_CHAT_ID</span> = <span class="val">{vars_dict["LOG_CHAT_ID"]}</span>')
    summary_lines.append(f'<span class="key">HANDLERS</span> = <span class="val">{vars_dict.get("HANDLERS", ". !")}</span>')
    summary_lines.append(f'<span class="key">PLUGIN_REPO</span> = <span class="val">{vars_dict.get("PLUGIN_REPO", "AstralBot/AstralModules")}</span>')

    summary_html = "<br>".join(summary_lines)

    warning_block = ""
    if not has_session and not has_bot_token:
        warning_block = """
        <div class="alert error">
          ⚠️ <strong>Cannot deploy:</strong> you skipped session creation
          and didn't provide a BOT_TOKEN. AstralBot needs at least one to
          start. Go back and either create a session, paste one, or provide
          a BOT_TOKEN.
        </div>
        """
        body = PAGE3_BODY_TEMPLATE.format(summary_html=summary_html, warning_block=warning_block)
        # Disable the deploy button by hiding it
        body = body.replace('<form method="post" action="/deploy">', '<form method="post" action="/deploy" onsubmit="return false;">')
        return _page_wrapper("Step 3", 3, body)

    if not has_session and has_bot_token:
        warning_block = """
        <div class="alert info">
          ℹ️ You skipped session creation. AstralBot will start in
          <strong>assistant-bot mode</strong> (using your BOT_TOKEN).
          You can add a userbot session later by DMing the bot
          <code>.session</code>.
        </div>
        """

    body = PAGE3_BODY_TEMPLATE.format(summary_html=summary_html, warning_block=warning_block)
    return _page_wrapper("Step 3", 3, body)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def find_free_port(default: int = 8080) -> int:
    """Try the default port, fall back to a free one.

    On HuggingFace Spaces, $PORT is set by HF and we MUST use it.
    """
    if is_hf_space():
        return int(os.environ.get("PORT", "7860"))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", default))
            return default
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def run_wizard(env_path: Path | str | None = None, auto_open: bool | None = None) -> int:
    """Launch the wizard. Blocks until the user clicks Deploy (or Ctrl+C).

    On HuggingFace Spaces (detected via SPACE_ID env var), the wizard binds
    to 0.0.0.0:$PORT (HF default 7860) and does NOT auto-open a browser —
    the user accesses the wizard via the HF Space URL.

    On local deploys, the wizard binds to 127.0.0.1:8080 and auto-opens
    the user's default browser.

    Returns 0 if the bot was started, 1 if the user cancelled.
    """
    if env_path is None:
        env_path = get_persistent_env_path()
    env_path = Path(env_path).resolve()
    env_path.parent.mkdir(parents=True, exist_ok=True)

    host = get_bind_host()
    port = find_free_port()
    app = make_app(env_path=env_path)

    # On HF Spaces, never auto-open a browser (the user accesses via HF URL)
    if auto_open is None:
        auto_open = not is_hf_space()

    # Build the URL displayed in the terminal
    if is_hf_space():
        space_id = os.environ.get("SPACE_ID", "")
        if space_id:
            # HF Spaces are accessible at https://{owner}-{space_name}.hf.space
            owner, _, name = space_id.partition("/")
            url = f"https://{owner}-{name}.hf.space/"
        else:
            url = f"http://0.0.0.0:{port}/"
    else:
        url = f"http://127.0.0.1:{port}/"

    print()
    print("=" * 60)
    print("  ✨ AstralBot Setup Wizard")
    print("=" * 60)
    if is_hf_space():
        print(f"  Detected: HuggingFace Spaces (SPACE_ID={os.environ.get('SPACE_ID')})")
        print(f"  Binding: {host}:{port}")
        print(f"  Wizard URL: {url}")
        print(f"  .env path: {env_path}")
        print()
        print("  Open the wizard URL above in your browser to configure AstralBot.")
        print("  After clicking Deploy, the bot starts in a background thread")
        print("  and the wizard keeps serving HTTP for HF Spaces health checks.")
    else:
        print(f"  Opening: {url}")
        print("  (If your browser doesn't auto-open, visit the URL manually.)")
    print("  Press Ctrl+C in this terminal to cancel.")
    print()

    if auto_open:
        # Open browser after a short delay (give Flask a moment to start)
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        # Disable Flask's default reloader and debug mode
        app.run(host=host, port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nWizard cancelled.")
        return 1
    return 0


def should_run_wizard(env_path: Path | str = ".env") -> bool:
    """Check whether the wizard should be launched.

    Returns True if .env is missing OR is missing API_ID / API_HASH.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        return True
    content = env_path.read_text(encoding="utf-8")
    has_api_id = False
    has_api_hash = False
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key == "API_ID" and len(line.split("=", 1)[1].strip()) > 0:
            has_api_id = True
        elif key == "API_HASH" and len(line.split("=", 1)[1].strip()) > 0:
            has_api_hash = True
    return not (has_api_id and has_api_hash)


if __name__ == "__main__":
    sys.exit(run_wizard())

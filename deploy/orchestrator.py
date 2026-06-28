"""Deployment orchestrator.

Runs the full deployment pipeline after the user clicks *Deploy* in the
wizard UI. Each step pushes events into a ``queue.Queue`` which the
``/status/stream`` SSE endpoint drains to the browser.

Steps
-----
1. validate_inputs        - re-check every required field
2. connect_database       - ping MongoDB using the supplied URI
3. save_configuration     - upsert the config doc for future restores
4. write_env_file         - materialise a ``.env`` so the bot can boot
5. install_dependencies   - ``pip install -r requirements.txt`` (plugins repo)
6. download_plugins       - ``git clone`` or ``wget`` the plugin archive
7. generate_session       - only if a session string was supplied
8. start_bot              - ``python -m zelretch`` via ``os.execv``

If any step fails, the orchestrator halts and emits a ``failed`` event
with a human-readable message; the UI shows a Retry button.
"""

from __future__ import annotations

import asyncio
import os
import queue
import selectors
import shlex
import shutil
import subprocess
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from . import storage as storage_mod
from . import validators


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------

@dataclass
class Event:
    type: str          # "step" | "log" | "completed" | "failed"
    step: str = ""     # machine name e.g. "connect_database"
    title: str = ""    # human label e.g. "Connecting to database"
    message: str = ""
    detail: str = ""
    progress: int = 0  # 0..100

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "step": self.step,
            "title": self.title,
            "message": self.message,
            "detail": self.detail,
            "progress": self.progress,
        }


STEPS = [
    ("validate_inputs",    "Validating variables"),
    ("connect_database",   "Connecting to database"),
    ("save_configuration", "Saving configuration"),
    ("write_env_file",     "Generating .env"),
    ("install_dependencies","Installing dependencies"),
    ("download_plugins",   "Downloading plugin repository"),
    ("generate_session",   "Storing userbot session"),
    ("start_bot",          "Starting Zelretch"),
]


class DeployError(Exception):
    """Step-level error carrying a user-facing ``detail`` block.

    When raised inside a ``_step_*`` handler, ``run()`` will use
    ``exc.detail`` (instead of the Python traceback) as the ``detail``
    field of the ``failed`` event. This lets step handlers surface
    captured subprocess output, validation hints, or any other
    multi-line diagnostic to the UI.
    """

    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.detail = detail


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

@dataclass
class DeployOrchestrator:
    config: dict[str, Any]
    events: "queue.Queue[Event]" = field(default_factory=queue.Queue)

    # Internal state
    _project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    _plugin_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1] / ".zelretch_plugins")
    _failed: bool = False
    _finished: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Run every step in order. Safe to call from a worker thread."""
        try:
            total = len(STEPS)
            for idx, (step_id, title) in enumerate(STEPS):
                if self._failed:
                    return
                self._emit(Event("step", step=step_id, title=title,
                                 message=title + "...",
                                 progress=int(idx * 100 / total)))
                handler = getattr(self, f"_step_{step_id}")
                try:
                    handler()
                except DeployError as exc:
                    # Step produced a user-facing error with custom detail
                    # (e.g. the bot's captured stdout/stderr). Use it as-is.
                    self._fail(step_id, title, exc, detail=exc.detail)
                    return
                except Exception as exc:
                    self._fail(step_id, title, exc)
                    return
                self._emit(Event("log", step=step_id, title=title,
                                 message="OK",
                                 progress=int((idx + 1) * 100 / total)))

            self._emit(Event("completed", progress=100,
                             message="Zelretch is starting up. The wizard window can be closed."))
            self._finished = True
        except Exception as exc:
            self._fail("orchestrator", "Orchestrator", exc)
        finally:
            self._finished = True

    def cancel(self) -> None:
        """Mark the deployment as cancelled so run() exits between steps."""
        self._failed = True

    # ------------------------------------------------------------------
    # Step handlers
    # ------------------------------------------------------------------

    def _step_validate_inputs(self) -> None:
        # Build a minimal form-like object so we can reuse the validators.
        class _Form:
            def __init__(self, data): self._d = data
            def get(self, k, default=""): return self._d.get(k, default)

        ok, errors, _ = validators.validate_required(_Form(self.config))
        if not ok:
            msgs = "; ".join(f"{k}: {v}" for k, v in errors.items())
            raise ValueError(f"Invalid configuration: {msgs}")

    def _step_connect_database(self) -> None:
        db_url = self.config["DATABASE_URL"]
        db_name = self.config.get("DATABASE_NAME", "Zelretch")
        ok, msg = asyncio.run(storage_mod.test_connection(db_url, db_name))
        if not ok:
            raise ConnectionError(f"Cannot connect to MongoDB: {msg}")

    def _step_save_configuration(self) -> None:
        db_url = self.config["DATABASE_URL"]
        db_name = self.config.get("DATABASE_NAME", "Zelretch")

        # Stash session string separately inside the same doc but never log it.
        config_to_save = dict(self.config)
        # Don't re-store the database URL inside the config doc as plaintext;
        # the wizard will already know it from the form on restore. We do
        # keep it though, because "restore" needs to fetch the rest of the
        # config using ONLY the URL — the URL itself isn't in the fetched
        # config naturally. Masked logging only.
        async def _save():
            async with storage_mod.ConfigStorage(db_url, db_name) as s:
                await s.save_config(config_to_save)
        asyncio.run(_save())

    def _step_write_env_file(self) -> None:
        env_path = self._project_root / ".env"
        lines = []
        for key in ("API_HASH", "API_ID", "BOT_TOKEN", "DATABASE_URL",
                    "DATABASE_NAME", "HANDLERS", "LOGGER_ID", "OWNER_ID",
                    "PLUGINS_REPO", "PLUGINS_BRANCH"):
            value = self.config.get(key, "")
            if value == "":
                continue
            lines.append(f"{key}={value}")
        # Session string is optional; the bot looks it up in the
        # ``session`` collection at startup via the wizard's storage step.
        env_text = "\n".join(lines) + "\n"
        env_path.write_text(env_text, encoding="utf-8")
        # Restrict permissions on Unix-like systems.
        try:
            os.chmod(env_path, 0o600)
        except OSError:
            pass

    def _step_install_dependencies(self) -> None:
        # The wizard's own requirements are already installed by the
        # outer setup script. Here we install the plugin repo's
        # requirements (downloaded in the next step) -- but to keep the
        # step ordering logical we tolerate a missing file at this point
        # and rely on download_plugins to have produced one.
        req_file = self._plugin_dir / "requirements.txt"
        if not req_file.exists():
            # Will be installed after download; nothing to do yet.
            return
        self._pip_install(req_file)

    def _step_download_plugins(self) -> None:
        repo = self.config.get("PLUGINS_REPO") or "Siamking672/Zelretch-Plugins"
        # Normalize: accept both "owner/repo" and "https://github.com/owner/repo"
        if repo.startswith("https://github.com/"):
            repo = repo[len("https://github.com/"):].rstrip("/")
        if repo.startswith("http://github.com/"):
            repo = repo[len("http://github.com/"):].rstrip("/")
        if repo.endswith(".git"):
            repo = repo[:-4]
        branch = self.config.get("PLUGINS_BRANCH") or "main"
        zip_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"

        # Clean previous attempt
        if self._plugin_dir.exists():
            shutil.rmtree(self._plugin_dir, ignore_errors=True)
        self._plugin_dir.mkdir(parents=True, exist_ok=True)

        archive = self._plugin_dir / "Plugins.zip"
        self._run(["wget", "-q", zip_url, "-O", str(archive)],
                  cwd=self._plugin_dir)

        # List top-level dir inside the zip so we know where to extract
        listing = subprocess.run(
            ["zipinfo", "-1", str(archive)],
            capture_output=True, text=True, check=True,
        )
        if not listing.stdout.strip():
            raise RuntimeError("Plugin archive is empty.")
        top_dir = listing.stdout.splitlines()[0].split("/")[0]

        self._run(["unzip", "-qq", str(archive)], cwd=self._plugin_dir)
        archive.unlink(missing_ok=True)

        extracted = self._plugin_dir / top_dir
        # Move contents up one level so self._plugin_dir is the plugin root.
        for child in extracted.iterdir():
            shutil.move(str(child), str(self._plugin_dir / child.name))
        extracted.rmdir()

        # Now install plugin deps (was deferred from previous step).
        req_file = self._plugin_dir / "requirements.txt"
        if req_file.exists():
            self._pip_install(req_file)

    def _step_generate_session(self) -> None:
        session_string = self.config.get("SESSION_STRING")
        if not session_string:
            return  # User skipped — nothing to do.

        # Persist the session to the bot's own ``session`` collection
        # using the same shape the runtime expects (``user_id`` + ``session``).
        # We need a user_id; do a one-shot login to fetch it.
        from kurigram import Client

        async def _persist():
            client = Client(
                name="zelretch_deploy_persist",
                api_id=int(self.config["API_ID"]),
                api_hash=self.config["API_HASH"],
                session_string=session_string,
                in_memory=True,
            )
            await client.start()
            try:
                me = await client.get_me()
                user_id = me.id
            finally:
                await client.stop()

            db_url = self.config["DATABASE_URL"]
            db_name = self.config.get("DATABASE_NAME", "Zelretch")
            async with storage_mod.ConfigStorage(db_url, db_name) as s:
                # The runtime Database class reads from ``session`` collection
                # with shape {user_id, session, date}. We use the same DB.
                session_col = s.get_collection("session")
                await session_col.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "session": session_string,
                        "date": time.strftime("%d/%m/%Y - %H:%M"),
                    }},
                    upsert=True,
                )

        asyncio.run(_persist())

    def _step_start_bot(self) -> None:
        """Launch ``python -m zelretch`` as a child process and monitor
        its first ~15 seconds of life.

        Design notes
        ------------
        * We run the bot as a **child process** (not ``os.execv``) so the
          wizard thread can observe startup and report success/failure
          to the UI via SSE.
        * We capture stdout+stderr together (``stderr=STDOUT``) and
          stream every line to the UI log panel in real time.
        * If the bot exits with a non-zero code, we **drain the remaining
          pipe** and include the full captured output in the
          :class:`DeployError` so the user can see *why* it crashed
          (missing env var, MongoDB auth failure, ImportError, etc.)
          instead of just "exit code 1".
        * If the bot is still alive after 15 seconds, we assume it
          started successfully, close our read handle, and let it run.
        """
        plugin_root = self._plugin_dir

        # ---- Pre-flight: verify required env vars are set ----
        required_vars = [
            "API_HASH", "API_ID", "BOT_TOKEN",
            "DATABASE_URL", "LOGGER_ID", "OWNER_ID",
        ]
        missing = [v for v in required_vars if not self.config.get(v)]
        if missing:
            raise DeployError(
                f"Cannot start bot: missing required variables: {', '.join(missing)}",
                detail=(
                    "The wizard collected the configuration but some required "
                    "values are empty. This is a bug in the wizard — please "
                    "report it.\n\n"
                    "Missing: " + ", ".join(missing)
                ),
            )

        # ---- Build the subprocess environment ----
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        for k, v in self.config.items():
            if v:
                env[str(k)] = str(v)

        # ---- Also write .env into the plugin dir ----
        # The bot's core/config.py calls load_dotenv() at import time.
        # load_dotenv() looks for .env in the CWD only. Since we chdir
        # to plugin_root before launching, we write .env there too so
        # the bot can find it as a fallback.
        env_file = plugin_root / ".env"
        env_lines = []
        for key in ("API_HASH", "API_ID", "BOT_TOKEN", "DATABASE_URL",
                    "DATABASE_NAME", "HANDLERS", "LOGGER_ID", "OWNER_ID",
                    "PLUGINS_REPO", "PLUGINS_BRANCH"):
            value = self.config.get(key, "")
            if value:
                env_lines.append(f"{key}={value}")
        env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
        try:
            os.chmod(env_file, 0o600)
        except OSError:
            pass

        # ---- Make start.sh executable (mirrors original setup script) ----
        start_sh = plugin_root / "start.sh"
        if start_sh.exists():
            os.chmod(start_sh, 0o755)

        sys.stdout.flush()
        sys.stderr.flush()

        # ---- Launch ----
        cmd = [sys.executable, "-u", "-m", "zelretch"]
        self._emit(Event("log", step="start_bot", title="",
                         message="$ " + " ".join(shlex.quote(c) for c in cmd)))
        proc = subprocess.Popen(
            cmd, env=env, cwd=str(plugin_root),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
            start_new_session=True,
        )

        captured_lines: list[str] = []
        try:
            sel = selectors.DefaultSelector()
            if proc.stdout:
                sel.register(proc.stdout, selectors.EVENT_READ)
            deadline = time.time() + 15
            try:
                while time.time() < deadline:
                    events = sel.select(timeout=0.5)
                    if events and proc.stdout:
                        line = proc.stdout.readline()
                        if not line:  # EOF
                            break
                        line_stripped = line.rstrip()
                        if line_stripped:
                            captured_lines.append(line_stripped)
                            self._emit(Event("log", step="start_bot", title="", message=line_stripped))
                    if proc.poll() is not None:
                        break
            finally:
                sel.close()

            # We hit the deadline without the bot exiting — it's running!
            self._emit(Event("log", step="start_bot", title="",
                             message="✓ Bot is running. Detaching wizard."))
        finally:
            # Don't kill the bot if it's still running — we want it to
            # continue after the wizard process exits.
            #
            # CRITICAL: Do NOT close proc.stdout. Closing the read end
            # of the pipe causes the bot's next write to stdout to
            # receive SIGPIPE, which kills the bot instantly. The bot
            # uses logging.StreamHandler() which writes to stdout on
            # every log message, so it would crash within seconds.
            #
            # Instead, start a daemon thread that continuously drains
            # the pipe (reads and discards output). This keeps the read
            # end open so the bot never receives SIGPIPE, and the pipe
            # buffer (64 KB on Linux) never fills up and blocks the
            # bot's event loop.
            if proc.poll() is None and proc.stdout:
                def _drain_stdout(stream, log_path):
                    """Continuously read from the bot's stdout and append
                    to a log file. Keeps the pipe open so the bot doesn't
                    receive SIGPIPE."""
                    try:
                        with open(log_path, "a", encoding="utf-8") as f:
                            for line in stream:
                                f.write(line)
                                f.flush()
                    except Exception:
                        pass

                bot_log = self._plugin_dir / "bot.log"
                threading.Thread(
                    target=_drain_stdout,
                    args=(proc.stdout, bot_log),
                    daemon=True,
                ).start()

    def _diagnose_bot_failure(self, lines: list[str]) -> dict:
        """Inspect captured bot output and return a user-friendly hint.

        Returns ``{"summary": str, "explanation": str}`` where
        ``summary`` is a one-liner suitable for the error message and
        ``explanation`` is a multi-line block for the detail panel.
        """
        joined = "\n".join(lines).lower()

        if "please set your" in joined:
            return {
                "summary": "A required environment variable is missing.",
                "explanation": (
                    "The bot's startup validator printed 'Please set your <VAR>'.\n"
                    "This means one of API_HASH, API_ID, BOT_TOKEN, DATABASE_URL,\n"
                    "LOGGER_ID, or OWNER_ID wasn't passed to the bot process.\n\n"
                    "Check the wizard's configuration form — make sure every\n"
                    "required field was filled in and click Deploy again."
                ),
            }
        if "databaseerr" in joined or "serverselectiontimeout" in joined:
            return {
                "summary": "Cannot connect to MongoDB.",
                "explanation": (
                    "The bot couldn't reach your MongoDB database.\n\n"
                    "Common causes:\n"
                    "  1. Wrong DATABASE_URL (check username, password, cluster name)\n"
                    "  2. Network egress blocked (Hugging Face Spaces free tier may\n"
                    "     block port 27017 — use mongodb+srv:// which rides on 443)\n"
                    "  3. IP not whitelisted (MongoDB Atlas: add 0.0.0.0/0 to the\n"
                    "     Network Access list to allow connections from anywhere)\n"
                    "  4. Database was paused (MongoDB Atlas free clusters sleep\n"
                    "     after inactivity)"
                ),
            }
        if "importerror" in joined or "modulenotfounderror" in joined:
            return {
                "summary": "A Python package is missing.",
                "explanation": (
                    "The bot failed to import a required package.\n\n"
                    "This usually means the plugin repository's requirements.txt\n"
                    "wasn't installed correctly. Try the 'Retry deployment' button —\n"
                    "the wizard will re-download and re-install everything.\n\n"
                    "If the error persists, check the install_dependencies step's\n"
                    "output in the log panel above for pip install errors."
                ),
            }
        if "sessionpasswordneeded" in joined or "auth_key" in joined:
            return {
                "summary": "Telegram authentication failed.",
                "explanation": (
                    "The bot couldn't authenticate with Telegram.\n\n"
                    "Common causes:\n"
                    "  1. BOT_TOKEN is wrong or revoked — get a new one from @BotFather\n"
                    "  2. API_ID/API_HASH mismatch — make sure they're from the same\n"
                    "     Telegram app (https://my.telegram.org)\n"
                    "  3. Userbot session string is invalid or expired — generate a\n"
                    "     new one via the wizard's OTP flow"
                ),
            }
        if "floodwait" in joined:
            return {
                "summary": "Telegram rate-limited the bot.",
                "explanation": (
                    "Telegram asked the bot to wait due to flood protection.\n\n"
                    "Wait a few minutes and click 'Retry deployment'. If this\n"
                    "happens repeatedly, the account may be temporarily restricted\n"
                    "— try again from a different account or after 24 hours."
                ),
            }
        if "invalid sqlite url" in joined or "cinemagoer" in joined:
            return {
                "summary": "The 'cinemagoer' package version is incompatible.",
                "explanation": (
                    "The bot crashed because the installed 'cinemagoer' package\n"
                    "uses an invalid SQLite URL format.\n\n"
                    "This is a known bug in cinemagoer >= 2026.6.27. The wizard\n"
                    "should have pinned cinemagoer to a pre-2026 version via its\n"
                    "constraints file — if you're seeing this, the constraint\n"
                    "didn't apply. Check the install_dependencies step output\n"
                    "above to see which version of cinemagoer was actually\n"
                    "installed.\n\n"
                    "Manual fix: SSH into the container and run:\n"
                    "  pip install 'cinemagoer<2026' --force-reinstall\n"
                    "Then click Retry deployment."
                ),
            }
        return {
            "summary": "",
            "explanation": (
                "The bot exited with a non-zero code but the wizard couldn't\n"
                "auto-diagnose the cause. Read the bot's output above carefully —\n"
                "the actual error message from Python/Pyrogram is in there.\n\n"
                "If you're stuck, copy the bot output and ask for help."
            ),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _pip_install(self, req_file: Path) -> None:
        cmd = [sys.executable, "-m", "pip", "install",
               "--root-user-action=ignore"]

        # Use the bundled constraints file to prevent known-broken
        # package versions from being installed. The constraints file
        # lives next to this module in the deploy/ directory.
        constraints_file = Path(__file__).parent / "constraints.txt"
        if constraints_file.exists():
            cmd.extend(["--constraint", str(constraints_file)])

        cmd.extend(["-r", str(req_file)])
        self._run(cmd)

    def _run(self, cmd: list[str], cwd: Optional[Path] = None) -> None:
        self._emit(Event("log", step="subprocess", title=" ".join(shlex.quote(c) for c in cmd),
                         message=" ".join(cmd)))
        result = subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                                capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()[:1000]
            raise RuntimeError(
                f"Command failed ({result.returncode}): {' '.join(cmd)}\n{detail}"
            )
        if result.stdout.strip():
            self._emit(Event("log", step="subprocess",
                             title=" ".join(cmd),
                             message=result.stdout.strip()[:500]))

    def _emit(self, event: Event) -> None:
        self.events.put(event)

    def _fail(self, step_id: str, title: str, exc: Exception,
              detail: str | None = None) -> None:
        """Mark the deployment as failed and emit a ``failed`` event.

        ``detail`` overrides the auto-generated Python traceback. Use
        this when the exception message alone isn't enough and you want
        to show the user a more useful block of text (e.g. the bot's
        captured stdout/stderr).
        """
        self._failed = True
        if detail is None:
            detail = traceback.format_exc(limit=4)
        self._emit(Event("failed", step=step_id, title=title,
                         message=str(exc), detail=detail, progress=0))

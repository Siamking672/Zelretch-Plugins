"""Flask application for the deployment wizard."""

from __future__ import annotations

import asyncio
import json
import queue
import threading
from typing import Any

from flask import (Flask, Response, jsonify, render_template, request,
                   stream_with_context)

from . import session_helper, storage as storage_mod, validators
from .orchestrator import DeployOrchestrator, Event


def create_app(initial_config: dict | None = None,
               auto_deploy: bool = False) -> Flask:
    app = Flask(__name__,
                template_folder="templates",
                static_folder="static")
    app.config["JSON_SORT_KEYS"] = False

    from .storage import mask as mask_sensitive_value
    app.jinja_env.globals["mask"] = mask_sensitive_value

    # ------------------------------------------------------------------
    # Per-process state. The wizard is single-user by design: it runs
    # locally on the deployer's machine and exits once the bot starts.
    # ------------------------------------------------------------------
    state: dict[str, Any] = {
        "config": dict(initial_config) if initial_config else {},
        "events": queue.Queue(),  # SSE event queue
        "orchestrator": None,
        "deploy_thread": None,
        "auto_restored": bool(initial_config),
        "_deploy_done": None,
        "auto_deploy_triggered": False,
    }

    # ------------------------------------------------------------------
    # Auto-deploy: if the config is complete and auto_deploy was
    # requested (e.g. Hugging Face Space restart with DATABASE_URL
    # set as a secret), kick off the deployment immediately in a
    # background thread — no user interaction required.
    # ------------------------------------------------------------------
    def _is_config_complete(cfg: dict) -> bool:
        """Check that every required variable has a non-empty value."""
        required = ["API_HASH", "API_ID", "BOT_TOKEN",
                    "DATABASE_URL", "LOGGER_ID", "OWNER_ID"]
        return all(cfg.get(k) for k in required)

    def _trigger_auto_deploy() -> None:
        """Start the orchestrator in a background thread."""
        if state.get("orchestrator") and not getattr(state["orchestrator"], "_finished", False):
            return  # Already running
        # Do NOT replace state["events"] here — the SSE generator may
        # already be reading from the existing queue. If we swap it out,
        # the generator reads from the old (empty) queue forever and
        # never sees any events. Just clear the done flag.
        state["_deploy_done"] = None
        orch = DeployOrchestrator(dict(state["config"]), state["events"])
        state["orchestrator"] = orch
        thread = threading.Thread(target=orch.run, daemon=True)
        state["deploy_thread"] = thread
        thread.start()

    if auto_deploy and _is_config_complete(state["config"]):
        # Mark immediately so the / route redirects to /status right away.
        state["auto_deploy_triggered"] = True
        # Delay the actual orchestrator start slightly so Flask is fully
        # ready to serve the status page when the user visits the URL.
        def _delayed_auto_deploy():
            import time
            time.sleep(2.0)
            print("Auto-deploy: starting deployment automatically "
                  "(config restored from database)...")
            _trigger_auto_deploy()

        threading.Thread(target=_delayed_auto_deploy, daemon=True).start()

    # ------------------------------------------------------------------
    # Step 0: intro page (new deployment vs restore)
    # ------------------------------------------------------------------
    @app.route("/")
    def intro():
        # If auto-deploy is in progress, redirect to the status page.
        if state["auto_deploy_triggered"]:
            from flask import redirect
            return redirect("/status")
        # If we auto-restored from DATABASE_URL, send the user straight
        # to the review page so they can hit Deploy without re-typing.
        if state["auto_restored"]:
            return render_template("review.html",
                                   config=state["config"],
                                   restored=True,
                                   auto_restored=True)
        return render_template("intro.html")

    # ------------------------------------------------------------------
    # Restore flow: enter DB URL, fetch saved config
    # ------------------------------------------------------------------
    @app.route("/restore", methods=["GET", "POST"])
    def restore():
        if request.method == "POST":
            db_url = (request.form.get("DATABASE_URL") or "").strip()
            db_name = (request.form.get("DATABASE_NAME") or "Zelretch").strip()
            ok, msg, storage = validators.validate_db_url(db_url, db_name)
            if not ok:
                return render_template("restore.html", error=msg, values=request.form)

            ok, config, msg = asyncio.run(
                storage_mod.fetch_saved_config(db_url, db_name)
            )
            if not ok:
                return render_template("restore.html", error=msg, values=request.form)
            if not config:
                return render_template("restore.html",
                                       error=msg or "No saved configuration found.",
                                       values=request.form)

            # Carry the DB URL forward so the user doesn't have to type it again.
            config.setdefault("DATABASE_URL", db_url)
            config.setdefault("DATABASE_NAME", db_name)
            state["config"] = config
            return render_template("review.html", config=config, restored=True)

        return render_template("restore.html")

    # ------------------------------------------------------------------
    # Step 1: required variables
    # ------------------------------------------------------------------
    @app.route("/step/required", methods=["GET", "POST"])
    def step_required():
        if request.method == "POST":
            ok, errors, cleaned = validators.validate_required(request.form)
            if not ok:
                return render_template("required.html",
                                       errors=errors, values=request.form)
            state["config"].update(cleaned)
            # Stash for the next step's prefill
            return render_template("userbot.html",
                                   api_id=cleaned.get("API_ID", ""),
                                   api_hash=cleaned.get("API_HASH", ""))
        return render_template("required.html")

    # ------------------------------------------------------------------
    # Step 2: optional userbot session
    # ------------------------------------------------------------------
    @app.route("/step/userbot", methods=["GET", "POST"])
    def step_userbot():
        if request.method == "POST":
            if request.form.get("action") == "skip":
                return render_template("review.html", config=state["config"])
            ok, errors, cleaned = validators.validate_userbot(request.form)
            if not ok:
                return render_template("userbot.html",
                                       errors=errors,
                                       values=request.form,
                                       api_id=state["config"].get("API_ID", ""),
                                       api_hash=state["config"].get("API_HASH", ""))
            state["config"].update(cleaned)
            return render_template("review.html", config=state["config"])
        # GET - prefill from saved config if available
        return render_template("userbot.html",
                               api_id=state["config"].get("API_ID", ""),
                               api_hash=state["config"].get("API_HASH", ""))

    # ------------------------------------------------------------------
    # Review + Deploy button
    # ------------------------------------------------------------------
    @app.route("/review")
    def review():
        return render_template("review.html", config=state["config"])

    @app.route("/api/deploy", methods=["POST"])
    def api_deploy():
        existing = state.get("orchestrator")
        if existing and not getattr(existing, "_finished", False):
            return jsonify({"ok": False, "error": "A deployment is already running."}), 409
        # Clear the done flag but do NOT replace the events queue —
        # the SSE generator may already be reading from it. The
        # orchestrator will push events into the existing queue.
        state["_deploy_done"] = None
        orch = DeployOrchestrator(dict(state["config"]), state["events"])
        state["orchestrator"] = orch
        thread = threading.Thread(target=orch.run, daemon=True)
        state["deploy_thread"] = thread
        thread.start()
        return jsonify({"ok": True})

    @app.route("/api/retry", methods=["POST"])
    def api_retry():
        # Cancel any orchestrator that may still be running, then reset.
        existing = state.get("orchestrator")
        if existing:
            existing.cancel()
        state["orchestrator"] = None
        state["_deploy_done"] = None
        return jsonify({"ok": True})

    # ------------------------------------------------------------------
    # Status page + SSE stream
    # ------------------------------------------------------------------
    @app.route("/status")
    def status_page():
        return render_template("status.html",
                               auto_deploy=state["auto_deploy_triggered"])

    @app.route("/status/stream")
    def status_stream():
        def generate():
            done = state.get("_deploy_done")
            if done:
                # On reconnect, send a minimal terminal event so the
                # browser knows the deployment is over. Include a
                # human-readable message so the UI doesn't show
                # "Unknown error" / "Failed: undefined".
                payload = {
                    "type": done,
                    "step": "",
                    "title": "Deployment " + ("completed" if done == "completed" else "failed"),
                    "message": ("The deployment has already finished. "
                                "Check the log above for details."
                                if done == "completed"
                                else "The deployment failed. Check the log above "
                                     "or click Retry to try again."),
                    "detail": "",
                    "progress": 100 if done == "completed" else 0,
                }
                yield f"data: {json.dumps(payload)}\n\n"
                return
            q = state["events"]
            last_progress = -1
            while True:
                try:
                    event: Event = q.get(timeout=15.0)
                except queue.Empty:
                    yield ": keepalive\n\n"
                    continue

                payload = event.to_dict()
                # Mask sensitive values that might leak via message or detail.
                payload["message"] = _mask_sensitive(payload.get("message", ""))
                payload["detail"] = _mask_sensitive(payload.get("detail", ""))

                if event.type in ("completed", "failed"):
                    state["_deploy_done"] = event.type
                    yield f"data: {json.dumps(payload)}\n\n"
                    break

                yield f"data: {json.dumps(payload)}\n\n"

        return Response(stream_with_context(generate()),
                        mimetype="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "X-Accel-Buffering": "no",
                            "Connection": "keep-alive",
                        })

    # ------------------------------------------------------------------
    # Interactive session creation endpoints
    # ------------------------------------------------------------------
    @app.route("/api/session/start", methods=["POST"])
    def session_start():
        data = request.get_json(silent=True) or request.form
        api_id = (data.get("API_ID") or "").strip()
        api_hash = (data.get("API_HASH") or "").strip()
        phone = (data.get("PHONE") or "").strip()
        try:
            ok, msg, session_id = session_helper.start_session_sync(api_id, api_hash, phone)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc)}), 400
        if not ok:
            return jsonify({"ok": False, "error": msg}), 400
        return jsonify({"ok": True, "session_id": session_id, "message": msg})

    @app.route("/api/session/verify", methods=["POST"])
    def session_verify():
        data = request.get_json(silent=True) or request.form
        session_id = (data.get("session_id") or "").strip()
        otp = (data.get("OTP") or "").strip()
        ok, msg, session_string, needs_password = session_helper.verify_otp_sync(session_id, otp)
        if not ok:
            return jsonify({"ok": False, "error": msg}), 400
        return jsonify({
            "ok": True,
            "message": msg,
            "session_string": session_string or "",
            "needs_password": needs_password,
        })

    @app.route("/api/session/password", methods=["POST"])
    def session_password():
        data = request.get_json(silent=True) or request.form
        session_id = (data.get("session_id") or "").strip()
        password = (data.get("PASSWORD") or "").strip()
        ok, msg, session_string = session_helper.submit_password_sync(session_id, password)
        if not ok:
            return jsonify({"ok": False, "error": msg}), 400
        return jsonify({"ok": True, "message": msg, "session_string": session_string})

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    @app.route("/healthz")
    def healthz():
        return jsonify({"ok": True})

    @app.route("/api/ping")
    def api_ping():
        """Browser-reachable health check.

        Useful for debugging "the wizard URL won't load" issues: visit
        ``/api/ping`` directly in the browser. If you get a JSON
        response, the wizard is reachable; if you don't, the issue is
        network/docker port-mapping, not the wizard.
        """
        import datetime
        import platform
        return jsonify({
            "ok": True,
            "service": "zelretch-wizard",
            "host": platform.node(),
            "time": datetime.datetime.utcnow().isoformat() + "Z",
        })

    @app.errorhandler(404)
    def not_found(_):
        return render_template("error.html",
                               error="Page not found.",
                               detail="The wizard step you tried to open does not exist."), 404

    return app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SENSITIVE_KEYS = ("BOT_TOKEN", "API_HASH", "DATABASE_URL", "SESSION_STRING", "PASSWORD")


def _mask_sensitive(text: str) -> str:
    """Best-effort scrub of sensitive values from log/error text."""
    if not text:
        return text
    out = text
    # Scrub lines like ``KEY=value`` where KEY is sensitive.
    for key in _SENSITIVE_KEYS:
        needle = f"{key}="
        idx = out.find(needle)
        while idx != -1:
            start = idx + len(needle)
            end = out.find("\n", start)
            if end == -1:
                end = len(out)
            out = out[:start] + "********" + out[end:]
            idx = out.find(needle, idx + 1)
    return out

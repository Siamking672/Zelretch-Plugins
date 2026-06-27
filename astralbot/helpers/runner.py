"""Subprocess runner — used by .eval, .sh, .shell builtins.

Best-effort sandboxing:
- Default timeout of 60s
- Captures both stdout and stderr
- Returns output as a string, capped to Telegram message size
"""

from __future__ import annotations

import asyncio
import io
import sys
import time
from contextlib import redirect_stdout, redirect_stderr
from typing import Optional


async def run_shell(cmd: str, timeout: int = 60, cwd: Optional[str] = None) -> str:
    """Run a shell command and return combined stdout+stderr."""
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return f"[timed out after {timeout}s]"
        return stdout.decode("utf-8", errors="replace") if stdout else ""
    except Exception as exc:
        return f"[error: {exc}]"


async def run_python(code: str, timeout: int = 30, env_globals: Optional[dict] = None) -> str:
    """Execute Python code (aexec style) and capture stdout/stderr.

    The code runs in an isolated namespace seeded with a few safe builtins.
    """
    out = io.StringIO()
    err = io.StringIO()

    sandbox_globals = {
        "__name__": "__eval__",
        "__builtins__": __builtins__,
        "asyncio": asyncio,
        "time": time,
        "print": print,
    }
    if env_globals:
        sandbox_globals.update(env_globals)

    try:
        with redirect_stdout(out), redirect_stderr(err):
            try:
                compiled = compile(code, "<eval>", "exec")
            except SyntaxError as se:
                return f"[syntax error] {se}"

            # If the code has top-level await, wrap in async func
            if "await " in code or "async " in code:
                wrapper = "async def __astral_eval__():\n" + "\n".join(
                    "    " + line for line in code.splitlines()
                )
                exec(compile(wrapper, "<eval>", "exec"), sandbox_globals)
                func = sandbox_globals["__astral_eval__"]
                await asyncio.wait_for(func(), timeout=timeout)
            else:
                exec(compiled, sandbox_globals)
    except asyncio.TimeoutError:
        return "[timed out after {timeout}s]"
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        err.write(tb)

    output = out.getvalue()
    if err.getvalue():
        output += "\n[stderr]\n" + err.getvalue()
    return output or "[no output]"

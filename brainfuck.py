# Zelretch Addons — Brainfuck interpreter
# Ported from UltroidAddons/brainfuck.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}bf <code>`
    Evaluate a Brainfuck program.

• `{i}bfencode <text>`
    Encode text into a Brainfuck program.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


def brainfuck_eval(code: str, max_steps: int = 1_000_000) -> str:
    tape = [0] * 30000
    ptr = 0
    pc = 0
    out = []
    steps = 0
    # Precompute matching brackets.
    pairs = {}
    stack = []
    for i, ch in enumerate(code):
        if ch == "[":
            stack.append(i)
        elif ch == "]":
            if not stack:
                raise ValueError("Unmatched ]")
            j = stack.pop()
            pairs[j] = i
            pairs[i] = j
    if stack:
        raise ValueError("Unmatched [")
    while pc < len(code):
        ch = code[pc]
        if ch == ">":
            ptr = (ptr + 1) % 30000
        elif ch == "<":
            ptr = (ptr - 1) % 30000
        elif ch == "+":
            tape[ptr] = (tape[ptr] + 1) % 256
        elif ch == "-":
            tape[ptr] = (tape[ptr] - 1) % 256
        elif ch == ".":
            out.append(chr(tape[ptr]))
        elif ch == ",":
            pass  # input not supported
        elif ch == "[":
            if tape[ptr] == 0:
                pc = pairs[pc]
        elif ch == "]":
            if tape[ptr] != 0:
                pc = pairs[pc]
        pc += 1
        steps += 1
        if steps > max_steps:
            raise RuntimeError("Step limit exceeded")
    return "".join(out)


def brainfuck_encode(text: str) -> str:
    """Generate a (very inefficient) Brainfuck program that prints ``text``."""
    out = []
    for ch in text:
        n = ord(ch)
        out.append("+" * n + ".>")
    return "".join(out)


@zelretch_cmd(pattern=r"bf( (.*)|$)")
async def bf_eval(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some Brainfuck code.`")
    try:
        result = brainfuck_eval(parts[1].strip())
        await eor(message, f"`{result or '(no output)'}`")
    except Exception as err:
        await eor(message, f"`{err}`")


@zelretch_cmd(pattern=r"bfencode ?(.*)")
async def bf_encode(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    code = brainfuck_encode(parts[1])
    if len(code) > 3500:
        code = code[:3500] + "…"
    await eor(message, f"```\n{code}\n```")

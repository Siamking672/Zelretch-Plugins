"""Kurigram namespace shim.

Kurigram 2.x ships its Python module under the ``pyrogram`` namespace
for drop-in compatibility with the original Pyrogram library — when you
``pip install kurigram``, the files land in ``site-packages/pyrogram/``
and there is no importable ``kurigram`` module.

This shim bridges that gap so the codebase can use native
``from kurigram import ...`` imports instead of ``from pyrogram ...``.

How it works
------------
When this package is imported, it replaces itself in ``sys.modules``
with the real ``pyrogram`` module (which IS Kurigram at runtime). From
that point on, ``import kurigram`` and ``from kurigram.types import X``
resolve to the exact same objects as their ``pyrogram`` counterparts —
they are the same module objects, not copies.

All submodules the project uses are pre-imported and aliased so that
nested imports like ``from kurigram.raw.functions.phone import X``
work without the caller needing to import each level manually.

pyroaddon compatibility
-----------------------
``pyroaddon`` monkey-patches ``pyrogram.Client`` to add ``ask()`` and
``listen()``. Because this shim aliases the real ``pyrogram`` module
(not a copy), the patched ``Client`` class is visible through both
``pyrogram.Client`` and ``kurigram.Client`` — they are the same object.

Future migration
----------------
When Kurigram 3.x ships a native ``kurigram`` top-level module, this
file can be deleted and every ``from kurigram import ...`` will keep
working unchanged.
"""

import sys

# Import pyrogram (which IS Kurigram at runtime). If pyrogram is not
# yet installed (e.g., _ensure_deps() hasn't run), raise a clear error
# rather than letting Python cache a broken `kurigram` entry in
# sys.modules — which would make every subsequent `import kurigram`
# fail even after pyrogram is installed.
try:
    import pyrogram
except ImportError as _exc:
    raise ImportError(
        "The 'kurigram' shim requires the 'pyrogram' module, which is "
        "provided by the 'kurigram' PyPI package. Install it with: "
        "pip install kurigram"
    ) from _exc

# Import every submodule the project uses so they are cached in
# sys.modules under their pyrogram.* names before we alias them.
import pyrogram.enums
import pyrogram.errors
import pyrogram.errors.exceptions
import pyrogram.file_id
import pyrogram.handlers
import pyrogram.filters
import pyrogram.types
import pyrogram.raw
import pyrogram.raw.base
import pyrogram.raw.types
import pyrogram.raw.functions
import pyrogram.raw.functions.channels
import pyrogram.raw.functions.messages
import pyrogram.raw.functions.phone
import pyrogram.raw.functions.stickers
import pyrogram.raw.functions.users

# Replace ourselves with the real pyrogram module. After this line,
# `kurigram` and `pyrogram` are the same object in sys.modules, so
# `from kurigram import Client` resolves to `pyrogram.Client`.
sys.modules[__name__] = pyrogram

# Alias every submodule so `from kurigram.X.Y.Z import Name` works.
# Each entry maps a `kurigram.*` path to the corresponding `pyrogram.*`
# module object that was imported above.
sys.modules["kurigram.enums"] = pyrogram.enums
sys.modules["kurigram.errors"] = pyrogram.errors
sys.modules["kurigram.errors.exceptions"] = pyrogram.errors.exceptions
sys.modules["kurigram.file_id"] = pyrogram.file_id
sys.modules["kurigram.handlers"] = pyrogram.handlers
sys.modules["kurigram.filters"] = pyrogram.filters
sys.modules["kurigram.types"] = pyrogram.types
sys.modules["kurigram.raw"] = pyrogram.raw
sys.modules["kurigram.raw.base"] = pyrogram.raw.base
sys.modules["kurigram.raw.types"] = pyrogram.raw.types
sys.modules["kurigram.raw.functions"] = pyrogram.raw.functions
sys.modules["kurigram.raw.functions.channels"] = pyrogram.raw.functions.channels
sys.modules["kurigram.raw.functions.messages"] = pyrogram.raw.functions.messages
sys.modules["kurigram.raw.functions.phone"] = pyrogram.raw.functions.phone
sys.modules["kurigram.raw.functions.stickers"] = pyrogram.raw.functions.stickers
sys.modules["kurigram.raw.functions.users"] = pyrogram.raw.functions.users

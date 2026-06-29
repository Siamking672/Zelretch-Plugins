# Zelretch Addons — Test plugin
# Sanity check — confirms the loader is wiring things up.

"""
✘ Commands Available

• `{i}test` — Sanity test command.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="test$")
async def test_handler(client, message):
    await eor(message, "✓ Zelretch addon loader is working.")

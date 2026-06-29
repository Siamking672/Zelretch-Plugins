# Zelretch Addons — Animated fonts (Pygments)
# Ported from UltroidAddons/fontsnew.py
# Copyright (C) 2021-2022 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}font <text>`
    Convert text to unicode decorative font.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor

FONTS = [
    str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩"),
    str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"),
    str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉"),
    str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ"),
    str.maketrans("abcdefghijklmnopqrstuvwxyz", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘϙʀꜱᴛᴜᴠᴡxʏᴢ"),
]


@zelretch_cmd(pattern=r"font ?(.*)")
async def font(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await eor(message, "`Give some text.`")
    text = parts[1].strip()
    lines = []
    for idx, table in enumerate(FONTS[:4], 1):
        lines.append(f"**{idx}:** {text.translate(table)}")
    await eor(message, "\n".join(lines))

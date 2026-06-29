# Zelretch Addons

<p align="center">
  <strong>Kurigram-compatible plugin repository for the Zelretch userbot.</strong>
</p>

This is the **separate addons repository** loaded by the
[Zelretch main project](https://github.com/TeamUltroid/Ultroid). It mirrors the
structure of the original
[UltroidAddons](https://github.com/TeamUltroid/UltroidAddons) but rewrites every
plugin to use Kurigram (Pyrogram fork) APIs instead of Telethon.

---

## How Zelretch loads these addons

1. On boot (or when you run `.updateaddons`), Zelretch clones this repository
   into `./addons/` (URL configurable via `ADDONS_URL` in your setup wizard).
2. The plugin loader scans every `*.py` file in `addons/` and imports each one.
3. Plugins register handlers using `@zelretch_cmd(pattern="...")` from
   `zelretch.core.decorators` — the same decorator the built-in plugins use.
4. Each plugin's `__doc__` string is parsed for the `✘ Commands Available` block
   and exposed via the `.help <plugin>` command.

For the full plugin architecture docs, see the
[main project's README](https://github.com/TeamUltroid/Ultroid).

---

## Available plugins

| Plugin | Commands | Description |
|---|---|---|
| `anime.py` | `.character <name>` | Anime character lookup via Jikan (MyAnimeList). |
| `astronomy.py` | `.apod` | NASA Astronomy Picture of the Day. |
| `autocorrect.py` | `.autocorrect <text>` | Auto-correct spelling with TextBlob. |
| `brainfuck.py` | `.bf <code>`, `.bfencode <text>` | Brainfuck interpreter + encoder. |
| `covid.py` | `.covid <country>` | COVID-19 statistics (disease.sh). |
| `encodedecode.py` | `.encode`, `.decode`, `.hexencode`, `.hexdecode`, `.urlencode`, `.urldecode` | Base64 / hex / URL codecs. |
| `fastly.py` | `.shorten <url>` | URL shortener (is.gd). |
| `figlet.py` | `.figlet <text>`, `.figletlist` | ASCII art via pyfiglet. |
| `findsong.py` | `.findsong <reply>` | Identify song (Shazam). |
| `fontsnew.py` | `.font <text>` | Decorative unicode fonts. |
| `fun.py` | `.slap`, `.hug`, `.8ball` | Fun interactive commands. |
| `hack.py` | `.hack` | Fake hacking animation (just for fun). |
| `howto.py` | `.howto <query>` | How-to summaries (Wikipedia). |
| `imdb.py` | `.imdb <movie>` | IMDB movie lookup (inline bot). |
| `morsecode.py` | `.morse`, `.demorse` | Morse code encoder/decoder. |
| `ncode.py` | `.ncode`, `.ndecode` | Numeric code encoder/decoder. |
| `ocr.py` | `.ocr <reply to image>` | Image to text via OCR.space. |
| `pokedex.py` | `.pokedex <pokemon>` | Pokemon stats via PokeAPI. |
| `qrcode.py` | `.qr <text>` | Generate QR codes. |
| `quotefancy.py` | `.quotefancy <text>` | Fancy quote image generator. |
| `random.py` | `.quote`, `.fact`, `.joke` | Random inspirational content. |
| `searchmsgs.py` | `.search <query>` | Search messages in the current chat. |
| `song.py` | `.lyrics <song>` | Song lyrics lookup. |
| `spam.py` | `.spam`, `.dspam` | Message spam (owner-only). |
| `spellcheck.py` | `.spell <word>` | Spell check (TextBlob). |
| `speechtool.py` | `.tts <text>` | Text-to-speech (gTTS). |
| `stickerspam.py` | `.kang`, `.stkrinfo` | Sticker tools. |
| `sticklet.py` | (placeholder) | Sticker text tool. |
| `test.py` | `.test` | Sanity test command. |
| `totalmsgs.py` | `.totalmsgs` | Count messages in the current chat. |
| `truthdare.py` | `.truth`, `.dare` | Truth or dare. |
| `waifu.py` | `.waifu` | Random waifu image. |
| `whichsong.py` | `.whichsong <reply>` | Alias for findsong. |
| `wikipedia.py` | `.wiki <query>` | Wikipedia search. |
| `wreplace.py` | `.wreplace <old> <new> <text>` | Word replacement. |
| `inline/pypi.py` | (inline query) `@assistant pypi <pkg>` | Inline PyPI search. |

---

## Writing a new addon

```python
# myplugin.py
"""
✘ Commands Available

• `{i}hello` — Say hello.
"""

from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern="hello$")
async def hello(client, message):
    await eor(message, "Hello from Zelretch addons!")
```

Drop the file into the repository root, commit, push, then run
`.updateaddons` inside Zelretch — the plugin is loaded automatically.

The `{i}` placeholder in the docstring is replaced with the configured command
handler at display time (default `.`).

---

## Requirements

Each plugin that needs extra pip packages should add them to
[`addons.txt`](addons.txt). The Zelretch loader installs addons.txt requirements
on first boot, then on every `.updateaddons`.

If a plugin's import fails (missing dep), the loader logs a warning and skips
that plugin — it does not crash the bot.

---

## Credits

These addons are a Kurigram port of the original
[UltroidAddons](https://github.com/TeamUltroid/UltroidAddons) by
[TeamUltroid](https://github.com/TeamUltroid).

- **Original authors:** TeamUltroid and UltroidAddons contributors
- **Original license:** AGPL v3
- **Zelretch port:** Zelretch Contributors (2026)

See [LICENSE](LICENSE) for the full AGPL v3 text and individual plugin headers
for in-line attribution (e.g. plugins ported from NiceGrill, DarkCobra, etc.).

<p align="center">
  <h1 align="center"><b>Zelretch Addons</b></h1>
</p>

<b>Community plugin repository for the Zelretch UserBot - Kurigram-based and compatible with the Zelretch plugin loader.</b>

[![Zelretch Addons](https://img.shields.io/badge/Zelretch-Addons-7c5cff)](#)
[![License](https://img.shields.io/badge/License-AGPLv3-blue)](LICENSE)
[![Based on UltroidAddons](https://img.shields.io/badge/Based%20on-UltroidAddons-critical)](https://github.com/TeamUltroid/UltroidAddons)

---

# What is this?

This repository contains the addon plugins that ship alongside
[Zelretch](https://github.com/TeamUltroid/Ultroid). Each `.py` file in the
root directory is a plugin that the Zelretch main project auto-loads when
the `ADDONS` config flag is `True` (the default).

The Zelretch plugin loader detects this folder in one of three locations:

1. `./addons/` (current working directory)
2. `./Zelretch-Addons/` (cloned next to the main repo)
3. `../Zelretch-Addons/` (cloned as a sibling)

so you can simply clone this repo next to the main one and Zelretch will
find it on the next start.

---

# Plugin catalogue

| Plugin | Command(s) | Description |
|--------|-----------|-------------|
| `anime.py` | `.character <name>` | Anime character lookup via Jikan / MyAnimeList. |
| `animechan.py` | `.animechan` | Random anime quote. |
| `astronomy.py` | `.astronomy` | NASA Astronomy Picture of the Day. |
| `autocorrect.py` | `.autocorrect <text>` | Auto-correct text via TextBlob. |
| `activitygen.py` | `.activitygen` | Suggest a random "last seen" activity. |
| `covid.py` | `.covid [country]` | COVID-19 statistics per country or globally. |
| `encodedecode.py` | `.encode` / `.decode <text>` | Base64 encode / decode. |
| `figlet.py` | `.figlet <text>` | ASCII art via pyfiglet. |
| `fontsnew.py` | `.fontsnew <text>` | Render text in a decorative unicode font. |
| `fun.py` | `.joke` | Random programming joke. |
| `hack.py` | `.hack` | Fake "hacking" animation. |
| `howto.py` | `.howto <query>` | DuckDuckGo instant-answer lookup. |
| `imdb.py` | `.imdb <keyword>` | IMDB lookup via inline bot. |
| `inline/pypi.py` | (inline) `@your_bot pypi <name>` | Inline PyPI package search. |
| `morsecode.py` | `.morse` / `.demorse <code>` | Morse code encoder / decoder. |
| `ocr.py` | `.ocr` (reply to image) | Optical character recognition via pytesseract. |
| `pokedex.py` | `.pokedex <name>` | Pokémon details via PokéAPI. |
| `quote.py` | `.quote` | Random inspirational quote. |
| `rng.py` | `.random [min] [max]` / `.coinflip` | Random number / coin flip. |
| `spam.py` | `.spam <n> <text>` / `.spamstick <n>` / `.dspam <delay> <n> <text>` | Repeat text or stickers. |
| `spellcheck.py` | `.spellcheck <word>` | Spell-check a single word. |
| `stickerspam.py` | `.stickerspam <n>` | Spam a replied sticker N times. |
| `truthdare.py` | `.truth` / `.dare` | Truth or dare prompts. |
| `typography.py` | `.typography <style> <text>` | Unicode typography (bold / italic / script / double-struck). |
| `wikipedia.py` | `.wiki <query>` | Wikipedia summary. |
| `wreplace.py` | `.wreplace <text>` | Replace whitespace with underscores. |

---

# Contributing

Pull requests are very welcome. Follow the format below when porting or
writing a new plugin:

```python
# Credits @username (creator of plugin and who ported)

# Ported from (if ported else skip)

# Ported for Zelretch < https://github.com/TeamUltroid/Ultroid >
```

Each plugin file should start with a docstring of the form:

```python
"""
✘ Commands Available -

• `{i}command <args>`
    One-line description shown by `.help <plugin>`.
"""
```

so the help system can pick it up.

---

# License

Zelretch Addons is licensed under the [GNU Affero General Public License v3 or later](LICENSE),
inherited from the original UltroidAddons project.

---

# Credits

Zelretch Addons is a rewrite of
[UltroidAddons](https://github.com/TeamUltroid/UltroidAddons) by
[TeamUltroid](https://t.me/TeamUltroid). The original authors retain all
credit for the plugin catalogue and community contributions.

> Made with 💕 by the Zelretch maintainers, on top of UltroidAddons by [@TeamUltroid](https://t.me/TeamUltroid).

import io
import os
import time
import urllib.request
from shutil import rmtree

import emoji
import requests
from bs4 import BeautifulSoup
from edge_tts import Communicate
from geopy.geocoders import Nominatim
from geopy.location import Location
from googlesearch import search
from googletrans import LANGCODES, LANGUAGES, Translator
from imdb import Cinemagoer, Movie
from pyrogram import Client
from pyrogram.types import InputMediaPhoto, Message
from wikipedia import exceptions, summary

from zelretch.functions.driver import Driver
from zelretch.functions.images import download_images
from zelretch.functions.paste import post_to_telegraph
from zelretch.functions.scraping import is_valid_url

from . import Config, HelpMenu, Symbols, db, handler, zelretch, on_message

imdb = Cinemagoer()
mov_titles = [
    "localized title",
    "canonical title",
    "smart canonical title",
    "smart long imdb canonical title",
    "long imdb canonical title",
    "long imdb title",
]

final_msg = """
<b>✦ 𝖳𝖬𝖴{}00𝖱𝖫 𝖨𝗇𝖿𝗈 𝖦𝖾𝗇𝗋𝖾𝗌 𝖱𝖺𝗍𝗂𝗇𝗀 𝖣𝗂�𝖾𝖼�𝗍��:</b> <code></code>
<b>✦ 𝖨𝖬𝖣𝖻 𝖴𝖱𝖫:</b> <a href='https://www.imdb.com/title/tt{1}'>Click here.</a>
<b>✦ 𝖠𝗂𝗋𝖽𝖺𝗍𝖾:</b> <code>{2}</code>
<b>✦ 𝖦𝖾𝗇𝗋𝖾𝗌:</b> <code>{3}</code>
<b>✦ 𝖱𝖺𝗍𝗂𝗇𝗀:</b> <code>{4}</code>
<b>✦ 𝖱𝗎𝗇𝗍𝗂𝗆𝖾:</b> <code>{5}</code>
<b>✦ 𝖣𝗂𝗋𝖾𝖼𝗍𝗈𝗋:</b> <code>{6}</code>

<b><a href='{7}'>💫 𝖬𝗈𝗋𝖾 𝖽𝖾𝗍𝖺𝗂𝗅𝗌 𝗁𝖾𝗋𝖾!</a></b>
"""

telegraph_msg = """
<img src='{0}'/>

<b>✦ 𝖳𝗂𝗍𝗅𝖾:</b> <code>{1}</code>
<b>✦ 𝖨𝖬𝖣𝖻 𝖴𝖱𝖫:</b> <a href='https://www.imdb.com/title/tt{2}'>Click here.</a>
<b>✦ 𝖠𝗂𝗋𝖽𝖺𝗍𝖾:</b> <code>{3}</code>
<b>✦ 𝖦𝖾𝗇𝗋𝖾𝗌:</b> <code>{4}</code>
<b>✦ 𝖱𝖺𝗍𝗂𝗇𝗀:</b> <code>{5}</code>
<b>✦ 𝖱𝗎𝗇𝗍𝗂𝗆𝖾:</b> <code>{6}</code>
<b>✦ 𝖣𝗂𝗋𝖾𝖼𝗍𝗈𝗋:</b> <code>{7}</code>
<b>✦ 𝖶𝗋𝗂𝗍𝖾𝗋:</b> <code>{8}</code>
<b>✦ 𝖢𝗈𝗆𝗉𝗈𝗌𝖾𝗋𝗌:</b> <code>{9}</code>
<b>✦ 𝖢𝖺𝗌𝗍:</b> <code>{10}</code>
<b>✦ 𝖢𝗈𝗎𝗇𝗍𝗋𝗒:</b> <code>{11}</code>
<b>✦ 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾:</b> <code>{12}</code>
<b>✦ 𝖡𝗈𝗑 𝖮𝖿𝖿𝗂𝖼𝖾:</b> <code>{13}</code>
<b>✦ 𝖯𝗅𝗈𝗍𝗋𝗌14𝖡𝗈𝗑 𝖮𝖿𝖿𝗂𝖼𝖾:</b> <


"""


@on_message("wikipedia", allow_master=True)
async def google_search(client: Client, message: Message):
    if len(message.command) < 2:
        return await zelretch.edit(message, "Give some text to search on wikipedia.")

    search_query = await zelretch.input(message)
    hell = await zelretch.edit(
        message, f"Searching for `{search_query}` on wikipedia..."
    )

    try:
        data = summary(search_query, auto_suggest=False)
    except exceptions.DisambiguationError as error:
        error = str(error).split("\n")
        result = "".join(
            f"`{i}`\n" if lineno > 1 else f"**{i}**\n"
            for lineno, i in enumerate(error, start=1)
        )
        return await hell.edit(f"**DisambiguationError:**\n\n{result}")
    except exceptions.PageError:
        return await zelretch.delete(hell, "**Page not found.**")

    await hell.edit(
        f"**𝖲𝖾𝖺𝗋𝖼𝗁:** `{search_query}`\n**𝖱𝖾𝗌𝗎𝗅𝗍:**\n{data}",
        disable_web_page_preview=True,
    )


@on_message("google", allow_master=True)
async def googleSearch(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.edit(message, "Give some text to search on google.")

    search_query = await zelretch.input(message)
    hell = await zelretch.edit(message, f"Searching for `{search_query}` on google...")

    try:
        results = search(search_query, 7, advanced=True)
    except Exception as error:
        return await zelretch.error(hell, f"`{str(error)}`")

    outStr = f"**🔍 𝖲𝖾𝖺𝗋𝖼𝗁:** `{search_query}`\n\n"
    for result in results:
        outStr += f"**🌐 𝖱𝖾𝗌𝗎𝗅𝗍:** [{result.title}]({result.url})\n"
        outStr += f"**📖 𝖣𝖾𝗌𝖼:** {str(result.description)[:50]}...\n\n"

    await hell.edit(outStr, disable_web_page_preview=True)


@on_message("reverse", allow_master=True)
async def reverseSearch(_, message: Message):
    if not message.reply_to_message:
        return await zelretch.edit(
            message, "Reply to an image/sticker to reverse search it."
        )

    hell = await zelretch.edit(message, "Processing...")
    if message.reply_to_message.sticker or message.reply_to_message.photo:
        dl_path = await message.reply_to_message.download(
            Config.DWL_DIR + "reverse.jpg"
        )
        file = {"encoded_image": (dl_path, open(dl_path, "rb"))}
    else:
        return await zelretch.error(
            hell, "Reply to an image/sticker to reverse search it."
        )

    await hell.edit("Searching on google...")

    resp = requests.post(
        "https://www.google.com/searchbyimage/upload", files=file, allow_redirects=False
    )

    webresp = requests.get(
        resp.headers.get("Location"),
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0",
        },
    )

    os.remove(dl_path)
    soup = BeautifulSoup(webresp.text, "html.parser")
    div = soup.find("div", {"class": "r5a77d"})
    if div:
        alls = div.find("a")
        link = alls["href"]
        text = alls.text

        await hell.edit(
            f"**𝖯𝗈𝗌𝗌𝗂𝖻𝗅𝖾 𝖱𝖾𝗌𝗎𝗅𝗍:** [{text}]({link})", disable_web_page_preview=True
        )
    else:
        return await hell.edit("No results found.")

    try:
        to_send = []
        images = await download_images(text, 3)

        for image in images:
            to_send.append(InputMediaPhoto(image))
        if to_send:
            await hell.reply_media_group(to_send)

        try:
            rmtree("./images")
        except:
            pass
    except:
        pass


@on_message("gps", allow_master=True)
async def gpsLocation(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.edit(message, "Give some place name to search.")

    search_query = await zelretch.input(message)
    hell = await zelretch.edit(
        message, f"Searching for `{search_query}` on google maps..."
    )

    geolocator = Nominatim(user_agent="Zelretch")
    location: Location = geolocator.geocode(search_query)

    if not location:
        return await zelretch.delete(hell, "Location not found.")

    latitiude = location.latitude
    longitude = location.longitude
    address = location.address

    await hell.reply_location(latitiude, longitude)
    await zelretch.delete(hell, f"**🌐 𝖯𝗅𝖺𝖼𝖾:** {address}")


@on_message("webshot", allow_master=True)
async def webScreenshot(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.edit(message, "Give some url to take screenshot.")

    search_query = await zelretch.input(message)
    if not is_valid_url(search_query):
        return await zelretch.edit(message, "Invalid url.")

    hell = await zelretch.edit(message, f"Taking screenshot of `{search_query}`...")
    driver, resp = Driver.get()
    if not driver:
        return await zelretch.error(hell, resp)

    driver.get(search_query)
    height = driver.execute_script(
        "return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);"
    )
    width = driver.execute_script(
        "return Math.max(document.body.scrollWidth, document.body.offsetWidth, document.documentElement.clientWidth, document.documentElement.scrollWidth, document.documentElement.offsetWidth);"
    )

    driver.set_window_size(width + 100, height + 100)
    image = driver.get_screenshot_as_png()
    Driver.close(driver)

    with io.BytesIO(image) as result:
        result.name = "Zelretch_Webshot.png"
        await hell.reply_document(result)
        await hell.delete()

    try:
        os.remove("Zelretch_Webshot.png")
    except:
        pass


@on_message("cricket", allow_master=True)
async def cricketScore(_, message: Message):
    BASE = "http://static.cricinfo.com/rss/livescores.xml"

    page = urllib.request.urlopen(BASE)
    soup = BeautifulSoup(page, "html.parser")
    result = soup.find_all("description")

    final = "**Cricket Live Score:\n\n**"
    for match in result:
        final += f"{Symbols.bullet} `{match.text}`\n\n"

    await zelretch.edit(message, final)


@on_message(["dictionary", "meaning"], allow_master=True)
async def wordMeaning(_, message: Message):
    BASE = "https://api.dictionaryapi.dev/api/v2/entries/en/{0}"
    if len(message.command) < 2:
        return await zelretch.edit(message, "Give some word to search.")

    search_query = await zelretch.input(message)
    hell = await zelretch.edit(message, f"Searching for `{search_query}`...")

    response = requests.get(BASE.format(search_query))
    if response.status_code == 404:
        return await zelretch.delete(hell, "Word not found.")

    data: dict = response.json()[0]

    outStr = ""
    outStr += f"**📖W:ord** `{data.get('word', search_query)}`\n"
    outStr += f"**🔊 Phonetic:** `{data.get('phonetic', 'Not Found')}`\n"

    for meaning in data.get("meanings", []):
        outStr += f"\n**{Symbols.bullet} Part of Speech:** `{meaning.get('partOfSpeech', 'Not Found').title()}`\n"
        for definition in meaning.get("definitions", []):
            outStr += f"    {Symbols.check_mark} `{definition.get('definition', 'Not Found')}`\n"
        synonyms = meaning.get("synonyms", [])
        outStr += "**👍 Synonyms:** " + ", ".join(synonyms) if synonyms else "Not Found"
        outStr += "\n"
        antonyms = meaning.get("antonyms", [])
        outStr += "**👎 Antonyms:** " + ", ".join(antonyms) if antonyms else "Not Found"
        outStr += "\n"

    audio = data.get("phonetics", [])[0].get("audio", "")
    if audio:
        await hell.reply_audio(audio, caption=outStr)
        await hell.delete()
    else:
        await hell.edit(outStr)


@on_message(["translate", "tr"], allow_master=True)
async def translateHandler(_, message: Message):
    if message.reply_to_message:
        if len(message.command) < 2:
            return await zelretch.edit(message, "Give some language code to translate.")
        toLang = message.command[1]
        text = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 2:
        msg = await zelretch.input(message)
        toLang = message.command[1]
        text = msg.split(" ", 1)[1]
    else:
        return await zelretch.delete(
            message,
            f"Either reply to a message with a language code or give input text and language code.\n\n**Example:** `{handler}tr en こんにちは世界`",
            15,
        )

    hell = await zelretch.edit(message, f"Translating to `{toLang}`...")
    text = emoji.demojize(text.strip())
    translator = Translator(http2=False)

    try:
        translated = translator.translate(text, toLang)
        outStr = f"**🌐 𝖳𝗋𝖺𝗇𝗌𝗅𝖺𝗍𝖾𝖽 𝖿𝗋𝗈𝗆** __{translated.src}__ **𝗍𝗈** __{translated.dest}__**:**"
        outStr += f"\n\n`{translated.text}`"
        await hell.edit(outStr)
    except Exception as e:
        return await zelretch.error(hell, f"`{str(e)}`")


@on_message("trcode", allow_master=True)
async def translateCodes(_, message: Message):
    outStr = None

    if len(message.command) > 1:
        language = message.command[1]
        fromCodeToLang = LANGUAGES.get(language.lower(), None)
        fromLangToCode = LANGCODES.get(language.lower(), None)

        if fromCodeToLang:
            outStr = f"**{Symbols.bullet} Language Code:** `{language.lower()}`\n**{Symbols.bullet} Language:** `{fromCodeToLang}`"
        elif fromLangToCode:
            outStr = f"**{Symbols.bullet} Language:** `{language.lower()}`\n**{Symbols.bullet} Language Code:** `{fromLangToCode}`"
        else:
            outStr = None

    if not outStr:
        outStr = "**Language Codes:**\n\n"
        for code in LANGUAGES:
            outStr += f"**{code}**: {LANGUAGES[code]}\n"

    await zelretch.edit(message, outStr)


@on_message(["voice", "tts"], allow_master=True)
async def textToSpeech(_, message: Message):
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 2:
        text = await zelretch.input(message)
    else:
        return await zelretch.delete(
            message,
            f"Either reply to a message with a language code or give input text and language code.\n\n**Example:** `{handler}tr en こんにちは世界`",
            15,
        )

    hell = await zelretch.edit(message, "Processing...")
    text = emoji.demojize(text.strip())

    try:
        comm = Communicate(
            text,
            "en-IN-NeerjaExpressiveNeural",
            rate="+10%",
            volume="+50%",
            pitch="+5Hz",
        )
        path = f"{Config.DWL_DIR}tts{int(time.time())}.mp3"
        await comm.save(path)

        await message.reply_audio(
            path,
            caption=f"**🔊 𝖵𝗈𝗂𝖼𝖾:** `{text[:100]}...`",
            performer="HellyAI",
            title="Zelretch TTS",
            thumb="./zelretch/resources/images/zelretch_logo.png",
        )
        await hell.delete()
    except Exception as e:
        return await zelretch.error(hell, f"`{str(e)}`")


@on_message("movie", allow_master=True)
async def movieSearch(_, message: Message):
    if len(message.command) < 2:
        return await zelretch.edit(message, "Give a movie name to search on IMDb.")

    query = await zelretch.input(message)
    hell = await zelretch.edit(message, "Searching...")
    try:
        movieObj: Movie.Movie = imdb.search_movie(query)[0]
        movieId = movieObj.movieID
        movieObj = imdb.get_movie(movieId)
        movieKeys = list(movieObj.keys())

        title = "No title found."
        for i in mov_titles:
            if i in movieKeys:
                title = movieObj[i]
                break

        airdate = "N/A"
        if "original air date" in movieKeys:
            airdate = movieObj["original air date"]
        elif "year" in movieKeys:
            airdate = movieObj["year"]

        runtime = movieObj.get("runtimes", ["N/A"])[0] + " min"
        rating = str(movieObj.get("rating", "N/A"))
        rating += " (by " + str(movieObj.get("votes", "N/A")) + " votes)"
        genres = ", ".join(movieObj.get("genres", ["N/A"]))
        countries = ", ".join(movieObj.get("countries", ["N/A"]))
        languages = ", ".join(movieObj.get("languages", ["N/A"]))
        plot = movieObj.get("plot outline", "N/A")
        cast = ", ".join([str(actor) for actor in movieObj.get("cast", ["N/A"])])
        directors = ", ".join(
            [str(actor) for actor in movieObj.get("director", ["N/A"])]
        )
        writers = ", ".join([str(actor) for actor in movieObj.get("writer", ["N/A"])])
        composers = ", ".join(
            [str(actor) for actor in movieObj.get("composer", ["N/A"])]
        )
        box_office_info = movieObj.get("box office", {})
        box_office = (
            "\n".join([f"{key} --> {value}" for key, value in box_office_info.items()])
            if box_office_info
            else "N/A"
        )
        image = movieObj.get("full-size cover url", None)
        link = post_to_telegraph(
            f"IMDb Search: {title}",
            telegraph_msg.format(
                image,
                title,
                movieId,
                airdate,
                genres,
                rating,
                runtime,
                directors,
                writers,
                composers,
                cast,
                countries,
                languages,
                box_office,
                plot,
            ),
        )
        await message.reply_photo(
            image,
            caption=final_msg.format(
                title, movieId, airdate, genres, rating, runtime, directors, link
            ),
            parse_mode="html",
        )
        await hell.delete()
    except IndexError:
        await zelretch.delete(hell, "No results found.")
    except Exception as e:
        await zelretch.error(hell, str(e))


HelpMenu("google").add(
    "wikipedia",
    "<query>",
    "Searches for the given query on wikipedia.",
    "wikipedia keanu reeves",
).add(
    "google", "<query>", "Searches for the given query on google.", "google the zelretch"
).add(
    "reverse",
    "<reply to image/sticker>",
    "Reverse searches the given image/sticker.",
    "reverse",
).add(
    "gps", "<place name>", "Sends the pin location of the given place.", "gps new york"
).add(
    "webshot",
    "<url>",
    "Takes a screenshot of the given url.",
    "webshot https://google.com",
).add(
    "cricket", None, "Sends the live cricket scores.", "cricket"
).add(
    "dictionary",
    "<word>",
    "Sends the meaning of the given word.",
    "dictionary loyalty",
    "An alias of 'meaning' can also be used.",
).add(
    "translate",
    "<lannguage code> <text/reply to message>",
    "Translates the given text to the given language code.",
    "translate en こんにちは世界",
    "An alias of 'tr' can also be used.",
).add(
    "trcode",
    "<language / code>",
    "Sends the language code and language name if found.",
    "trcode en",
    "If no language code is given, sends all the language codes.",
).add(
    "voice",
    "<text/reply to message>",
    "Sends the text as a voice message.",
    "voice I'm Helly and this is an Text to Speech Example.",
    "An alias of 'tts' can also be used.",
).add(
    "movie",  # Bugged: to-be-fixed
    "<movie name>",
    "Sends the details of the given movie.",
    "movie the shawshak redemption",
).info(
    "Every Google command you need."
).done()

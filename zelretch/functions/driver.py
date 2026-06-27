import datetime
import os
import random
import time
from urllib.parse import quote_plus

import httpx
import requests
from pytz import country_names, country_timezones, timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import \
    presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait

from zelretch.core import ENV, Config, db

from .formatter import format_text


class ChromeDriver:
    def __init__(self) -> None:
        self.carbon_theme = [
            "3024-night",
            "a11y-dark",
            "blackboard",
            "base16-dark",
            "base16-light",
            "cobalt",
            "duotone-dark",
            "hopscotch",
            "lucario",
            "material",
            "monokai",
            "night-owl",
            "nord",
            "oceanic-next",
            "one-light",
            "one-dark",
            "panda-syntax",
            "paraiso-dark",
            "seti",
            "shades-of-purple",
            "solarized+dark",
            "solarized+light",
            "synthwave-84",
            "twilight",
            "verminal",
            "vscode",
            "yeti",
            "zenburn",
        ]

    def get(self):
        if not Config.CHROME_BIN:
            return (
                None,
                "ChromeBinaryErr: No binary path found! Install Chromium or Google Chrome.",
            )

        try:
            options = Options()
            options.binary_location = Config.CHROME_BIN
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--disable-gpu")
            options.add_argument("--headless=new")
            options.add_argument("--test-type")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1920x1080")
            options.add_experimental_option(
                "prefs", {"download.default_directory": "./"}
            )
            service = Service(Config.CHROME_DRIVER)
            driver = webdriver.Chrome(options, service)
            return driver, None
        except Exception as e:
            return None, f"ChromeDriverErr: {e}"

    def close(self, driver: webdriver.Chrome):
        driver.close()
        driver.quit()

    @property
    def get_random_carbon(self) -> str:
        url = "https://carbon.now.sh/?l=auto"
        url += f"&t={random.choice(self.carbon_theme)}"
        url += f"&bg=rgba%28{random.randint(1, 255)}%2C{random.randint(1, 255)}%2C{random.randint(1, 255)}%2C1%29"
        url += "&code="
        return url

    async def generate_carbon(
        self, driver: webdriver.Chrome, code: str, is_random: bool = False
    ) -> str:
        filename = f"{round(time.time())}"
        BASE_URL = (
            self.get_random_carbon
            if is_random
            else "https://carbon.now.sh/?l=auto&code="
        )

        driver.get(BASE_URL + format_text(quote_plus(code)))
        driver.command_executor._commands["send_command"] = (
            "POST",
            "/session/$sessionId/chromium/send_command",
        )
        params = {
            "cmd": "Page.setDownloadBehavior",
            "params": {"behavior": "allow", "downloadPath": Config.DWL_DIR},
        }
        driver.execute("send_command", params)

        driver.find_element(By.XPATH, "//button[@id='export-menu']").click()
        driver.find_element(By.XPATH, "//input[@title='filename']").send_keys(filename)
        driver.find_element(By.XPATH, "//button[@id='export-png']").click()

        return f"{Config.DWL_DIR}/{filename}.png"


class ClimateDriver:
    def __init__(self) -> None:
        self.weather_api = "https://api.openweathermap.org/data/2.5/weather?lat={0}&lon={1}&appid={2}&units=metric"
        self.location_api = (
            "https://api.openweathermap.org/geo/1.0/direct?q={0}&limit=1&appid={1}"
        )
        self.pollution_api = "http://api.openweathermap.org/data/2.5/air_pollution?lat={0}&lon={1}&appid={2}"
        self.AQI_DICT = {
            1: "Good",
            2: "Fair",
            3: "Moderate",
            4: "Poor",
            5: "Very Poor",
        }

    async def fetchLocation(self, city: str, apiKey: str):
        response = httpx.get(self.location_api.format(city, apiKey))
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0]["lat"], data[0]["lon"]
        return None, None

    async def fetchWeather(self, city: str, apiKey: str):
        lattitude, longitude = await self.fetchLocation(city, apiKey)
        if not lattitude and not longitude:
            return None

        response = httpx.get(self.weather_api.format(lattitude, longitude, apiKey))
        if response.status_code == 200:
            return response.json()
        return None

    async def fetchAirPollution(self, city: str, apiKey: str):
        lattitude, longitude = await self.fetchLocation(city, apiKey)
        if not lattitude and not longitude:
            return None

        response = httpx.get(self.pollution_api.format(lattitude, longitude, apiKey))
        if response.status_code == 200:
            return response.json()
        return None

    async def getTime(self, timestamp: int) -> str:
        tz = await db.get_env(ENV.time_zone) or "Asia/Kolkata"
        tz = timezone(tz)
        return datetime.datetime.fromtimestamp(timestamp, tz=tz).strftime("%I:%M %p")

    def getCountry(self, country_code: str) -> str:
        return country_names.get(country_code, "Unknown")

    def getCountryTimezone(self, country_code: str) -> str:
        timezones = country_timezones.get(country_code, [])
        if timezones:
            return ", ".join(timezones)
        return "Unknown"

    def getWindData(self, windSpeed: str, windDegree: str) -> str:
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        ix = round(windDegree / (360.00 / len(dirs)))
        kmph = str(float(windSpeed) * 3.6) + " km/h"
        return f"[{dirs[ix % len(dirs)]}] {kmph}"


class SCRAP_DATA:
    """Class to get and handel scrapped data"""

    def __init__(self, urls: list[str] | str) -> None:
        self.urls = urls
        self.path = "./scrapped/"
        if not os.path.isdir(self.path):
            os.makedirs("./scrapped/")

    def get_images(self) -> list:
        images = []
        if isinstance(self.urls, str):
            requested = requests.get(self.urls)
            try:
                name = self.path + f"img_{time.time()}.jpg"
                with open(name, "wb") as f:
                    f.write(requested.content)
                images.append(name)
            except Exception as e:
                requested.close()
        else:
            for i in self.urls:
                if i:
                    requested = requests.get(i)
                else:
                    continue
                try:
                    name = self.path + f"img_{time.time()}.jpg"
                    with open(name, "wb") as f:
                        f.write(requested.content)
                    images.append(name)
                except Exception as e:

                    requested.close()
                    continue
        return images

    def get_videos(self) -> list:
        videos = []
        if isinstance(self.urls, str):
            if i:
                requested = requests.get(i)
            else:
                return []
            try:
                name = self.path + f"vid_{time.time()}.mp4"
                with open(name, "wb") as f:
                    f.write(requested.content)
                videos.append(name)
            except Exception as e:
                requested.close()
        else:
            for i in self.urls:
                if i:
                    requested = requests.get(i)
                else:
                    continue
                try:
                    name = self.path + f"vid_{time.time()}.mp4"
                    with open(name, "wb") as f:
                        f.write(requested.content)
                    videos.append(name)
                except Exception as e:

                    requested.close()
                    continue
        return videos


class INSTAGRAM(ChromeDriver):
    """Class to scrap data from instagram"""

    def __init__(self, url: str) -> None:
        self.url = url
        self.article = "article._aa6a"
        self.ul_class = "_acay"
        self.image_class = "x5yr21d"
        self.video_class = "x1lliihq"
        self.next_button = "button._afxw"
        self.return_dict = {"image": [], "video": []}
        super().__init__()

    def get_all(self):
        driver, error = self.get()
        if not driver:
            return error

        driver.get(self.url)
        wait = WebDriverWait(driver, 30)
        image_links = []
        video_links = []
        try:
            element = wait.until(presence_of_element_located(
                (By.CLASS_NAME, self.ul_class)))

            while True:
                sub_element = element.find_elements(
                    By.CLASS_NAME, self.image_class)
                for i in sub_element:
                    url = i.get_attribute("src")
                    image_links.append(url)

                sub_element = element.find_elements(
                    By.CLASS_NAME, self.video_class)
                for i in sub_element:
                    url = i.get_attribute("src")
                    video_links.append(url)

                try:
                    driver.find_element(
                        By.CSS_SELECTOR, self.next_button).click()
                except:  # Failed to either find the element or click on next i.e. no more media left in post
                    break
        except:
            element = wait.until(presence_of_element_located((By.CSS_SELECTOR, self.article)))
            try:
                sub_element = element.find_element(By.TAG_NAME, "img")
                url = sub_element.get_attribute("src")
                image_links.append(url)
            except:
                sub_element = element.find_element(By.TAG_NAME, "video")
                url = sub_element.get_attribute("src")
                video_links.append(url)

        self.close(driver)
        # To remove duplicates here I am converting into set
        if image_links:
            image_links = list(set(image_links))
        if video_links:
            video_links = list(set(video_links))
            for i in video_links:
                image_links.remove(i)

        self.return_dict.get("image").extend(image_links)
        self.return_dict.get("video").extend(video_links)
        return self.return_dict


Driver = ChromeDriver()
Climate = ClimateDriver()

"""Image manipulation helpers.

Only the functions still used by remaining plugins are kept here:

* ``convert_to_png``       — used by ``telegraph`` plugin.
* ``add_rounded_corners``  — used internally by ``generate_alive_image``.
* ``generate_alive_image`` — used by the ``bot`` plugin's ``.alive`` cmd.
* ``remove_bg``            — used by the ``utilities`` plugin.

Functions that were only used by now-deleted plugins (logo, images,
media, google) have been removed: ``get_wallpapers``, ``make_logo``,
``deep_fry``, ``draw_meme``, ``create_gradient``, ``create_calendar``,
``create_thumbnail``, ``download_images``.
"""

import os
import time

import httpx
from PIL import Image, ImageDraw, ImageFont, ImageOps
from unidecode import unidecode

from .formatter import format_text


def convert_to_png(image: str) -> str:
    output_img = f"png_{round(time.time())}.png"

    img = Image.open(image)
    img.save(output_img, "PNG")
    img.close()

    os.remove(image)
    return output_img


def add_rounded_corners(img: Image.Image, radius: int = 80):
    circle = Image.new("L", (radius * 2, radius * 2), 0)

    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)

    alpha = Image.new("L", img.size, 255)
    w, h = img.size

    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
    alpha.paste(
        circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius)
    )

    img.putalpha(alpha)

    return img


def generate_alive_image(
    username: str, profile_pic: str, del_img: bool, font_path: str
) -> str:
    if not profile_pic.endswith(".png"):
        profile_pic = convert_to_png(profile_pic)

    img = Image.open(profile_pic).convert("RGBA")
    img_rotated = img.rotate(45, expand=True)

    width, height = img_rotated.size
    left = width / 2 - 480 / 2
    top = height / 2 - 480 / 2
    right = width / 2 + 480 / 2
    bottom = height / 2 + 480 / 2

    cropped_img = img_rotated.crop((left, top, right, bottom))

    img_rotated = ImageOps.fit(
        cropped_img, (480, 480), method=0, bleed=0.0, centering=(0.5, 0.5)
    )

    img_rounded = add_rounded_corners(img_rotated)

    img = img_rounded.rotate(-45, expand=True)

    background = Image.open("./zelretch/resources/images/zelretch_alive.png").convert(
        "RGBA"
    )

    background.paste(img, (383, 445), img)
    draw = ImageDraw.Draw(background)

    text = format_text(username[:25] + ("..." if len(username) > 25 else ""))

    font_size = width // 15
    font = ImageFont.truetype(font_path, font_size, encoding="utf-8")

    text_length = draw.textlength(text, font)
    position = ((background.width - text_length) / 2, background.height - 145)
    draw.text(
        position,
        unidecode(text),
        (255, 255, 255),
        font,
    )

    output_img = f"alive_{int(time.time())}.png"
    background.save(output_img, "PNG")
    background.close()

    if del_img:
        os.remove(profile_pic)

    return output_img


async def remove_bg(api_key: str, image: str) -> str:
    response = httpx.post(
        "https://api.remove.bg/v1.0/removebg",
        files={"image_file": open(image, "rb")},
        data={"size": "auto"},
        headers={"X-Api-Key": api_key},
    )
    filename = f"removedbg_{int(time.time())}.png"

    if response.is_success:
        with open(filename, "wb") as f:
            f.write(response.content)
    else:
        raise Exception(
            f"RemoveBGError: [{response.status_code}] {response.content.decode('utf-8')}"
        )

    return filename

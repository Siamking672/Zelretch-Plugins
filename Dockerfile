FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    CHROME_BIN=/usr/bin/chromium \
    CHROME_DRIVER=/usr/bin/chromedriver

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        chromium \
        chromium-driver \
        curl \
        ffmpeg \
        fonts-dejavu-core \
        git \
        mediainfo \
        p7zip-full \
        unzip \
        wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m pip install --upgrade pip setuptools wheel \
    && python3 -m pip install -r requirements.txt

COPY setup ./setup
RUN chmod +x ./setup

CMD ["bash", "./setup"]

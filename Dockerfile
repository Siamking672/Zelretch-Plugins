FROM python:3.11-slim

# System deps commonly needed by plugins (ffmpeg for media, git for updates,
# chromium for scraping, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
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

ENV CHROME_BIN=/usr/bin/chromium \
    CHROME_DRIVER=/usr/bin/chromedriver \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOCKER=True

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source
COPY . .

# Create data directories
RUN mkdir -p userdata/plugins userdata/downloads userdata/temp userdata/external_plugins

# HuggingFace Spaces REQUIRES the container to run as a non-root user with UID 1000.
# Create that user and chown the app directory.
# On HF Spaces, /data is mounted as persistent storage (if enabled) and is
# owned by UID 1000 automatically.
RUN if id -u 1000 >/dev/null 2>&1; then \
        echo "User with UID 1000 already exists"; \
    else \
        useradd -m -u 1000 -s /bin/bash astral; \
    fi && \
    chown -R 1000:1000 /app

# Switch to non-root user
USER 1000

# HuggingFace Spaces default port. The wizard auto-detects HF Spaces via
# the SPACE_ID env var and binds to 0.0.0.0:$PORT.
# Locally (without SPACE_ID), the wizard binds to 127.0.0.1:8080 instead.
ENV PORT=7860
EXPOSE 7860

# Single command. If .env is missing, the wizard auto-launches.
# If .env is present, the bot starts directly.
CMD ["python", "-m", "astralbot"]

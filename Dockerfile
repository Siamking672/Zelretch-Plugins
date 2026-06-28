FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

# System packages required by the wizard (browser automation, downloads,
# media processing). The plugin repo assumes these exist at runtime.
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
        zip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install wizard dependencies first (they change less often).
COPY requirements.txt ./
RUN python3 -m pip install --upgrade pip setuptools wheel \
    && python3 -m pip install -r requirements.txt

# Copy the wizard, the kurigram namespace shim, and entry points.
# The kurigram/ directory MUST be copied — it's the shim package that
# lets the codebase use `from kurigram import ...` instead of
# `from pyrogram import ...`. Without it, every deploy.* module that
# imports kurigram will fail with ModuleNotFoundError at startup.
COPY deploy ./deploy
COPY kurigram ./kurigram
COPY deploy.py ./
COPY setup ./
RUN chmod +x ./setup

# Expose both ports so the same Dockerfile works in every context:
#   * 7860  -> Hugging Face Spaces (which only forwards port 7860 to
#              the public hf.space URL). The wizard auto-detects HF
#              via the SPACE_AUTHOR_NAME / SPACE_REPO_NAME env vars
#              and listens on 0.0.0.0:7860.
#   * 8765  -> Local Docker / VPS. The wizard picks a free port in
#              the 8765..8785 range and binds to 127.0.0.1 (or
#              ZELRETCH_WIZARD_HOST if overridden).
EXPOSE 7860 8765

CMD ["bash", "./setup"]

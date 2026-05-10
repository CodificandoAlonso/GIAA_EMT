FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    curl \
    wget \
    unzip \
    bash \
    bc \
    procps \
    git \
    build-essential \
    gcc \
    g++ \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    openjdk-21-jdk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir ./WEB_DEVEL && mkdir ./GAMA

COPY WEB_DEVEL ./WEB_DEVEL

COPY GAMA ./GAMA


RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r /app/WEB_DEVEL/bash_scripts/requirements.txt

WORKDIR /app/WEB_DEVEL

RUN npm ci --omit=dev

WORKDIR /opt

RUN wget https://github.com/gama-platform/gama/releases/download/2025.06.4/GAMA_2025.06.4_Linux.zip \
    && unzip GAMA_2025.06.4_Linux.zip \
    && rm GAMA_2025.06.4_Linux.zip

RUN chmod +x /app/WEB_DEVEL/bash_scripts/*.sh && chmod +x /opt/headless/gama-headless.sh


WORKDIR /app

ENV GAMA_SOURCE_DIR=/workspace/GAMA/src/TEST_MOBILITY/models \
    LOGS_DIR=/workspace/WEB_DEVEL/data/logs \
    KNOWN_DATA_DIR=/workspace/WEB_DEVEL/data/known_data \
    SCRIPTS_DIR=/app/WEB_DEVEL/bash_scripts \
    STATE_DIR=/workspace/WEB_DEVEL/bash_scripts \
    LAST_SIMULATION_FILE=/workspace/WEB_DEVEL/bash_scripts/.last_simulation

EXPOSE 3000

ENTRYPOINT ["node", "/app/WEB_DEVEL/src/server.js"]
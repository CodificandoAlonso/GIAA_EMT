# ==========================================================================
# Multi-stage build. Only the runtime stage ends up in the final image: no
# compiler, JDK, git or download tools are shipped.
#
#   c-build  -> compiles C_REWRITE/simulation (needs C_REWRITE/.env-development,
#               which is gitignored and must exist in the build context)
#   gama     -> downloads and unpacks GAMA 2025.06.4 (Linux, without bundled JDK)
#   web-deps -> npm ci (express/socket.io are pure JS, so node_modules is portable)
#   runtime  -> Java 21 JRE (required by GAMA 2025.06) + Node + Python
# ==========================================================================

# ----------------------------- C engine ----------------------------------
FROM gcc:14-bookworm AS c-build

WORKDIR /build/C_REWRITE
COPY C_REWRITE/Makefile C_REWRITE/.env-* ./
COPY C_REWRITE/src ./src
RUN make release


# ----------------------------- GAMA --------------------------------------
FROM ubuntu:24.04 AS gama

ARG GAMA_VERSION=2025.06.4

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl unzip \
    && rm -rf /var/lib/apt/lists/*

# The zip unpacks at its root (headless/, plugins/, Gama.ini, ...), so it is
# extracted into /opt/gama and copied to /opt in the runtime stage, keeping
# /opt/headless/gama-headless.sh where run_simulation.sh expects it.
RUN curl -fsSL -o /tmp/gama.zip \
        "https://github.com/gama-platform/gama/releases/download/${GAMA_VERSION}/GAMA_${GAMA_VERSION}_Linux.zip" \
    && mkdir -p /opt/gama \
    && unzip -q /tmp/gama.zip -d /opt/gama \
    && rm /tmp/gama.zip \
    && chmod +x /opt/gama/headless/gama-headless.sh


# ----------------------------- Web deps ----------------------------------
FROM node:20-bookworm-slim AS web-deps

WORKDIR /deps
COPY WEB_DEVEL/package.json WEB_DEVEL/package-lock.json ./
RUN npm ci --omit=dev


# ----------------------------- Runtime -----------------------------------
# Ubuntu 24.04 based; glibc is required by GAMA's Equinox launcher, so Alpine
# is not an option. gama-headless.sh uses the `java` found in PATH.
FROM eclipse-temurin:21-jre-noble AS runtime

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    bc \
    procps \
    python3 \
    python3-venv \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY --from=gama /opt/gama/ /opt/

WORKDIR /app

COPY WEB_DEVEL ./WEB_DEVEL
COPY GAMA ./GAMA
COPY C_REWRITE ./C_REWRITE
COPY BASE_DATA ./BASE_DATA
COPY --from=c-build /build/C_REWRITE/simulation /app/C_REWRITE/simulation
COPY --from=web-deps /deps/node_modules /app/WEB_DEVEL/node_modules

RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir -r /app/WEB_DEVEL/bash_scripts/requirements.txt

# data/logs is excluded from the build context (see .dockerignore) and mounted
# as a volume by docker-compose; create it so the image also works standalone.
RUN chmod +x /app/WEB_DEVEL/bash_scripts/*.sh && mkdir -p /app/WEB_DEVEL/data/logs

ENV EMT_C_BIN=/app/C_REWRITE/simulation \
    EMT_C_DATA_REF=/app/C_REWRITE/data

WORKDIR /app

ENV GAMA_SOURCE_DIR=/app/GAMA/src/TEST_MOBILITY/models \
    LOGS_DIR=/app/WEB_DEVEL/data/logs \
    KNOWN_DATA_DIR=/app/WEB_DEVEL/data/known_data \
    SCRIPTS_DIR=/app/WEB_DEVEL/bash_scripts \
    STATE_DIR=/app/WEB_DEVEL/bash_scripts \
    LAST_SIMULATION_FILE=/app/WEB_DEVEL/bash_scripts/.last_simulation

EXPOSE 3000

ENTRYPOINT ["node", "/app/WEB_DEVEL/src/server.js"]

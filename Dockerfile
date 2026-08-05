# Astrolab headless MCP server. The runtime uses in-process pyswisseph with verified Swiss
# Ephemeris data and needs no calculation sidecar.

ARG PYTHON_IMAGE=python:3.13-slim@sha256:bf503bb2243c5aad0aa951544dd60d165f992646441d35dea90893703fc26251

# --- Stage 1: fetch + verify ephemeris data ------------------------------------------------
FROM ${PYTHON_IMAGE} AS ephe
# The data revision and file hashes are fixed release inputs.
ARG DM0LZ_REF=e164fced7699f0c574836895660f8f6f9b9c4bb8
WORKDIR /ephe
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY infra/ephe/MANIFEST.sha256 .
RUN while read -r hash name; do \
      curl -fsSL -o "$name" "https://raw.githubusercontent.com/dm0lz/swiss-ephemeris-mcp-server/${DM0LZ_REF}/vendor/swisseph/$name"; \
    done < MANIFEST.sha256 \
    && sha256sum -c MANIFEST.sha256

# --- Stage 2: build Python environment -------------------------------------------------------
FROM ${PYTHON_IMAGE} AS builder
ARG UV_VERSION=0.7.19
WORKDIR /app
# build-essential: pyswisseph may lack a cp313 manylinux wheel and compile from source.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "uv==${UV_VERSION}"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --group engine-a --no-install-project

# --- Stage 3: non-root runtime ---------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime
ARG SOURCE_COMMIT=unknown
LABEL org.opencontainers.image.revision="${SOURCE_COMMIT}"
WORKDIR /app
RUN groupadd --gid 10001 astrolab \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /home/astrolab \
        --shell /usr/sbin/nologin astrolab
COPY --from=builder --chown=10001:10001 /app/.venv /app/.venv
COPY --chown=10001:10001 astro/ astro/
COPY --from=ephe /ephe/*.se1 /app/ephe/

ENV PATH="/app/.venv/bin:${PATH}" \
    HOME=/home/astrolab \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SWISS_ENGINE=a \
    SWISS_EPHE_PATH=/app/ephe \
    ASTRO_MCP_TRANSPORT=http \
    ASTRO_MCP_HOST=0.0.0.0 \
    ASTRO_MCP_PORT=8400
EXPOSE 8400
USER 10001:10001
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 8400), 2).close()"

CMD ["python", "-m", "astro.server"]

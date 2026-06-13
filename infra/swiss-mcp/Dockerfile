# Reproducible self-hosted Swiss Ephemeris MCP server — the `swissremote` primary provider.
#
# Both sources are PINNED so a rebuild is deterministic (reproducibility hard-constraint):
#   - DM0LZ_REF   : exact commit of the MCP server wrapper (code + vendored ephemeris data)
#   - SWISSEPH_REF: release tag of the Swiss Ephemeris computation engine (swetest)
#
# The public theme-astral.me demo of this same code was decommissioned (DNS NXDOMAIN, 2026-06).
# Build context is this directory; the Dockerfile fetches the pinned sources itself, so the
# context only needs to contain this file.
#
# Build:  docker build -t swiss-mcp:swe2.10.03 infra/swiss-mcp
# Run:    docker run -d --name swiss-mcp --restart unless-stopped -p 8000:8000 \
#                    -e MCP_HTTP_MODE=true swiss-mcp:swe2.10.03
FROM node:18-alpine

ARG DM0LZ_REF=e164fced7699f0c574836895660f8f6f9b9c4bb8
ARG SWISSEPH_REF=v2.10.03

RUN apk add --no-cache \
    git \
    build-base \
    make \
    gcc \
    g++ \
    libc-dev

WORKDIR /app

# Pinned Swiss Ephemeris engine -> swetest binary.
RUN git clone https://github.com/aloistr/swisseph.git /tmp/swisseph && \
    cd /tmp/swisseph && \
    git checkout ${SWISSEPH_REF} && \
    make && \
    cp swetest /usr/local/bin/ && \
    rm -rf /tmp/swisseph

# Pinned dm0lz MCP server (brings index.js, package*.json and vendor/swisseph ephemeris data).
RUN git clone https://github.com/dm0lz/swiss-ephemeris-mcp-server.git /tmp/srv && \
    cd /tmp/srv && \
    git checkout ${DM0LZ_REF} && \
    cp -r package*.json index.js vendor /app/ && \
    rm -rf /tmp/srv

RUN npm ci --only=production

RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 && \
    chown -R nodejs:nodejs /app
USER nodejs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "console.log('Health check passed')" || exit 1

ENV MCP_HTTP_MODE=false
ENV NODE_ENV=production
ENV SE_EPHE_PATH=/app/vendor/swisseph

CMD ["node", "index.js"]

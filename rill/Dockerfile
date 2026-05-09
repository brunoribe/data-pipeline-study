FROM debian:bookworm-slim

ENV PATH=/root/.rill:${PATH}

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git unzip \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    install -d /root/.rill; \
    arch="$(uname -m)"; \
    case "${arch}" in \
        x86_64) platform="linux_amd64" ;; \
        aarch64|arm64) platform="linux_arm64" ;; \
        *) echo "Unsupported architecture: ${arch}" >&2; exit 1 ;; \
    esac; \
    version="$(curl -fsSL https://cdn.rilldata.com/rill/latest.txt)"; \
    archive="rill_${platform}.zip"; \
    curl -fsSL "https://cdn.rilldata.com/rill/${version}/${archive}" -o "/tmp/${archive}"; \
    curl -fsSL "https://cdn.rilldata.com/rill/${version}/checksums.txt" -o /tmp/checksums.txt; \
    (cd /tmp && grep "rill_${platform}.zip" checksums.txt | sha256sum -c -); \
    unzip -q "/tmp/${archive}" -d /tmp/rill-bin; \
    install -m 755 /tmp/rill-bin/rill /root/.rill/rill; \
    rm -rf "/tmp/${archive}" /tmp/checksums.txt /tmp/rill-bin; \
    /root/.rill/rill runtime install-duckdb-extensions

WORKDIR /srv/project

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
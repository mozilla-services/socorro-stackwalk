# https://hub.docker.com/_/rust/
FROM rust:1.63.0-bullseye@sha256:4d6b7664f5292cdfbeaa7eb9f1f4eae01aa289a49e4f043cdf6f4f63d0cf8ca8

ARG groupid=10001
ARG userid=10001

WORKDIR /app/

RUN update-ca-certificates && \
    groupadd --gid $groupid app && \
    useradd -g app --uid $userid --shell /usr/sbin/nologin --create-home app && \
    chown app:app /app/

USER app

# Copy everything over
COPY --chown=app:app . /app/

ENTRYPOINT ["/app/bin/entrypoint.sh"]

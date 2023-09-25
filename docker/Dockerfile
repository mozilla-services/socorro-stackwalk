# https://hub.docker.com/_/rust/
FROM rust:1.72.1-bookworm@sha256:6a2ac38604fce995fd586c8d760147f71d9113dcbe84a7fcddcb30c60a1ec7ee

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

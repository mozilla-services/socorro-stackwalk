# https://hub.docker.com/_/rust/
FROM rust:1.69.0-bullseye@sha256:0996206db384a076bbd96411eb738047b1d978d41e0184cb5ebcb37edf988362

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

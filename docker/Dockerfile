# https://hub.docker.com/_/rust/
FROM rust:1.84.1-bookworm@sha256:738ae99a3d75623f41e6882566b4ef37e38a9840244a47efd4a0ca22e9628b88

ARG groupid=10001
ARG userid=10001

WORKDIR /app/

RUN apt update && apt install -y python3-venv

RUN update-ca-certificates && \
    groupadd --gid $groupid app && \
    useradd -g app --uid $userid --shell /usr/sbin/nologin --create-home app && \
    chown app:app /app/

USER app

# Copy everything over
COPY --chown=app:app . /app/

ENTRYPOINT ["/app/bin/entrypoint.sh"]

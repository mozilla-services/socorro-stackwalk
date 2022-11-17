# https://hub.docker.com/_/rust/
FROM rust:1.65.0-bullseye@sha256:6c20d87766142d058f3e21874fe1db426c49ce3e1575c8c300fdc27d06db92a9

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

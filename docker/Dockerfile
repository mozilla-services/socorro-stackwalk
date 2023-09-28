# https://hub.docker.com/_/rust/
# NOTE(willkg): we want to use an older debian image so that we're not locked
# into a newer glibc
FROM rust:1.72.1-bullseye@sha256:6562d50b62366d5b9db92b34c6684fab5bf3b9f627e59a863c9c0675760feed4

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

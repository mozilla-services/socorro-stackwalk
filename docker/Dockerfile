# https://hub.docker.com/_/rust/
# NOTE(willkg): we want to use bullseye debian image so that we're not locked
# into a newer glibc which doesn't work with docker in our infrastructure.
# We can update to a newer debian image once we've moved to GCP.
FROM rust:1.76.0-bullseye@sha256:b3ec72b36c32f9c2437714354fadf2d05988acd3333699145e0a539c524bde99

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

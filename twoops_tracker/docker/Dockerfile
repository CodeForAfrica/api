FROM python:3.10-slim-bullseye AS python-base

RUN apt-get update \
    && apt-get -y upgrade \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

FROM twoopstracker/app:deps AS app-deps

FROM twoopstracker/app:srcs AS app-srcs

FROM python-base AS python-app

WORKDIR /app

RUN mkdir -p media staticfiles logs

COPY --from=app-deps /app ./
COPY --from=app-srcs /app ./

COPY twoops_tracker/sh/cmd.sh ./
RUN chmod +x ./cmd.sh

EXPOSE 8000

ENTRYPOINT ["./cmd.sh"]
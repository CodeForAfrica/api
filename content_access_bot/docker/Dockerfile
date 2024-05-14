FROM python:3.11-slim-bullseye AS python-base
FROM content_access_bot/app:deps AS app-deps
FROM content_access_bot/app:srcs AS app-srcs
FROM python-base AS python-app

WORKDIR /app
COPY  content_access_bot/docker/app.json ./
COPY --from=app-deps /app ./
COPY --from=app-srcs /app ./

CMD ["tail", "-f", "/dev/null"]

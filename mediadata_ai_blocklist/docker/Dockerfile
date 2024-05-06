FROM python:3.11-slim-bullseye AS python-base
FROM mediadata_ai_blocklist/app:deps AS app-deps
FROM mediadata_ai_blocklist/app:srcs AS app-srcs
FROM python-base AS python-app

WORKDIR /app
COPY  mediadata_ai_blocklist/docker/app.json ./
COPY --from=app-deps /app ./
COPY --from=app-srcs /app ./

CMD ["tail", "-f", "/dev/null"]

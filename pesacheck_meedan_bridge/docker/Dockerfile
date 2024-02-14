FROM python:3.11-slim-bullseye AS python-base
FROM pesacheck_meedan_bridge/app:deps AS app-deps
FROM pesacheck_meedan_bridge/app:srcs AS app-srcs
FROM python-base AS python-app

WORKDIR /app
COPY pesacheck_meedan_bridge/docker/app.json ./
COPY --from=app-deps /app ./
COPY --from=app-srcs /app ./

CMD ["/bin/bash", "-f"]

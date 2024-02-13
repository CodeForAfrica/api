FROM python:3.11-slim-bullseye AS python-base
FROM python-base AS python-app

FROM pesacheck_meedan_bridge/app:deps AS app-deps
FROM pesacheck_meedan_bridge/app:srcs AS app-srcs

WORKDIR /app

COPY . /app

COPY --from=app-deps /app ./
COPY --from=app-srcs /app ./

ENV PATH="/root/.local/bin:$PATH"

CMD ["./pex"]

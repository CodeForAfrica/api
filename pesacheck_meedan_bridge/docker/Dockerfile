FROM python:3.9-slim-bullseye AS python-base
FROM pesacheck_meedan_bridge/app:deps AS app-deps
FROM pesacheck_meedan_bridge/app:srcs AS app-srcs
FROM python-base AS python-app

WORKDIR /app
COPY . /app

COPY --from=app-deps /app ./
COPY --from=app-srcs /app ./

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y \ 
    curl=7.74.0-1.3+deb11u11 \
    cron=3.0pl1-137 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash \
    && echo '0 0 * * * root /bin/bash -c "SHELL=/bin/bash  /app/pex && echo \"Cron job ran at $(date)\" >> /app/debug.log"' > /etc/cron.d/crontab \
    && chmod 0644 /etc/cron.d/crontab \
    && crontab /etc/cron.d/crontab

ENV PATH="/root/.local/bin:$PATH"

CMD ["cron", "-f"]

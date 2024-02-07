FROM python:3.9-slim-bullseye AS python-base
FROM pesacheck_meedan_bridge/app:deps AS app-deps
FROM pesacheck_meedan_bridge/app:srcs AS app-srcs
FROM python-base AS python-app

WORKDIR /app
COPY . /app

COPY --from=app-deps /app ./
COPY --from=app-srcs /app ./

RUN apt-get update && apt-get install -y curl --no-install-recommends

RUN curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get -y install cron
RUN echo '* * * * * root /bin/bash -c "SHELL=/bin/bash  /app/pex && echo \"Cron job ran at $(date)\" >> /app/debug.log"' > /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

RUN crontab /etc/cron.d/crontab

CMD ["cron", "-f"]

FROM python:3.10-slim as deps

COPY twoops_tracker.py/main.pex /main.pex
RUN PEX_TOOLS=1 /usr/local/bin/python3.10 /main.pex venv --scope=deps --compile /bin/dj


FROM python:3.10-slim as srcs

COPY twoops_tracker.py/main.pex /main.pex
RUN PEX_TOOLS=1 /usr/local/bin/python3.10 /main.pex venv --scope=srcs --compile /bin/dj


FROM python:3.10-slim

ENV APP_DOCKER=/app

# Expose server port
EXPOSE 8000

### Volumes
WORKDIR ${APP_DOCKER}

RUN mkdir -p media staticfiles logs

COPY twoops_tracker/sh/*.sh /
RUN chmod +x /cmd.sh

COPY --from=deps /bin/dj /bin/dj
COPY --from=srcs /bin/dj /bin/dj

### Run app
ENTRYPOINT ["/cmd.sh"]

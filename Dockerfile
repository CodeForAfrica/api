# Multi-stage build

###############################################################################
## Python base image
###############################################################################
FROM python:3.8-slim AS python-base

### Arg
ARG DEBIAN_FRONTEND=noninteractive

### Env
ENV APP_HOST=.
ENV APP_DOCKER=/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

### Dependencies
#### System
####  We need libpq-dev in both build and final runtime image
RUN apt-get update \
    && apt-get -y upgrade --fix-missing\
    && apt-get install libpq-dev --no-install-recommends -y \
    && apt-get clean

###############################################################################
## Python builder base image
###############################################################################
FROM python-base AS python-builder-base

### Dependencies
#### System
RUN apt-get install gcc python-dev --no-install-recommends -y \
    && apt-get clean \
    && pip install --upgrade pip

###############################################################################
## Python builder ci image
###############################################################################
FROM python-builder-base AS python-builder-ci

### Env
ENV PATH=/root/.local/bin:$PATH

### Dependencies
#### Python dev & testing
COPY ${APP_HOST}/requirements-all.txt ${APP_HOST}/requirements-dev.txt /tmp/
RUN pip install --user -r /tmp/requirements-dev.txt

###############################################################################
## Python app ci image
###############################################################################
FROM python-base AS python-app-ci

### Env
ENV PATH=/root/.local/bin:$PATH

### Dependencies
#### Python (copy from python-builder)
COPY --from=python-builder-ci /root/.local /root/.local
#### git (for `pre-commit`)
#### postgresql-client (for `psql`)
RUN apt-get install git postgresql-client --no-install-recommends -y \
    && apt-get clean

# Expose server port
EXPOSE 8000

### Volumes
WORKDIR ${APP_DOCKER}
RUN mkdir -p media staticfiles logs

### Setup app
COPY ${APP_HOST} ${APP_DOCKER}
COPY ${APP_HOST}/contrib/docker/cmd.sh ${APP_HOST}/contrib/docker-compose/wait-for-postgres.sh /
RUN chmod +x /cmd.sh \
    && chmod +x /wait-for-postgres.sh

### Run app-ci
CMD ["/cmd.sh"]

###############################################################################
## Python builder image
###############################################################################

FROM python-builder-base AS python-builder

### Env
ENV PATH=/root/.local/bin:$PATH

### Dependencies
#### Python
COPY ${APP_HOST}/requirements-all.txt ${APP_HOST}/requirements.txt /tmp/
RUN pip install --user -r /tmp/requirements.txt

###############################################################################
## Python app image
###############################################################################
FROM python-base AS python-app

### Env
ENV PATH=/root/.local/bin:$PATH

### Dependencies
#### Python (copy from python-builder)
COPY --from=python-builder /root/.local /root/.local

# Expose server port
EXPOSE 8000

### Volumes
WORKDIR ${APP_DOCKER}
RUN mkdir -p media staticfiles logs

### Setup app
COPY ${APP_HOST} ${APP_DOCKER}
COPY ${APP_HOST}/contrib/docker/*.sh /
RUN chmod +x /cmd.sh

### Run app
CMD ["/cmd.sh"]

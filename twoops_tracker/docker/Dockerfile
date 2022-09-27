FROM python:3.10-slim

### Arg
ARG DEBIAN_FRONTEND=noninteractive

### Env
ENV APP_HOST=.
ENV APP_DOCKER=/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV STATIC_ROOT=/app/staticfiles

COPY twoops_tracker.py/main.pex /bin/dj

# Expose server port
EXPOSE 8000

### Volumes
WORKDIR ${APP_DOCKER}
RUN mkdir -p media staticfiles logs

COPY twoops_tracker/sh/*.sh /
RUN chmod +x /cmd.sh

### Run app
CMD ["/cmd.sh"]

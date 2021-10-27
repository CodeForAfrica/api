#!/bin/sh
python manage.py migrate --noinput               # Apply database migrations
python manage.py collectstatic --noinput         # Collect static files

# Prepare log files and start outputting logs to stdout
touch /app/logs/gunicorn.log
touch /app/logs/access.log
tail -n 0 -f /app/logs/*.log &

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers=${TWOOPS_TRACKER_GUNICORN_WORKERS:-3} \
    --worker-class gevent \
    --log-level=${TWOOPS_GUNICORN_LOG_LEVEL:-warning} \
    --timeout=${TWOOPS_GUNICORN_TIMEOUT:-60} \
    --log-file=/app/logs/gunicorn.log \
    --access-logfile=/app/logs/access.log \
    --name twoopsTracker \
    ${TWOOPSTRACKER_GUNICORN_EXTRA_CONFIG:-} \
    twoopstracker.wsgi:application

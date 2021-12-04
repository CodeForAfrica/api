#!/bin/sh
python manage.py migrate --noinput               # Apply database migrations
python manage.py collectstatic --noinput         # Collect static files

# Prepare log files and start outputting logs to stdout
touch /app/logs/gunicorn.log
touch /app/logs/access.log
touch /app/logs/celery.log

tail -n 0 -f /app/logs/*.log &

# Start celery worker
celery -A twoopstracker worker -l INFO &> /app/logs/celery.log &

until timeout 10s celery -A twoopstracker inspect ping; do
    >&2 echo "Celery workers not available"
done

echo 'Starting flower'
celery -A project flower

celery -A twoopstracker flower -l INFO &> /app/logs/celery.log &

# everytime the container is restarted, the scheduler will reset
rm -rf celerybeat-schedule
# Start celery beat service
celery -A twoopstracker beat -l INFO &> /app/logs/celery.log &

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

#!/bin/sh
/bin/dj/pex manage migrate --noinput       # Apply database migrations
/bin/dj/pex manage collectstatic --noinput # Collect static files

# Prepare log files and start outputting logs to stdout
touch /app/logs/gunicorn.log
touch /app/logs/access.log
touch /app/logs/celery.log

tail -n 0 -f /app/logs/*.log &

# Start celery worker
/bin/dj/pex celery -A twoopstracker worker -l INFO >/dev/null 2>/app/logs/celery.log &

# everytime the container is restarted, the scheduler will reset
rm -rf celerybeat-schedule
# Start celery beat service
/bin/dj/pex celery -A twoopstracker beat -l INFO >/dev/null 2>/app/logs/celery.log &

# Start Gunicorn processes
echo Starting Gunicorn.
exec /bin/dj/pex gunicorn \
	--bind 0.0.0.0:8000 \
	--workers="${TWOOPS_TRACKER_GUNICORN_WORKERS:-3}" \
	--worker-class gevent \
	--log-level="${TWOOPS_GUNICORN_LOG_LEVEL:-warning}" \
	--timeout="${TWOOPS_GUNICORN_TIMEOUT:-60}" \
	--log-file=/app/logs/gunicorn.log \
	--access-logfile=/app/logs/access.log \
	--name twoopsTracker \
	"${TWOOPSTRACKER_GUNICORN_EXTRA_CONFIG:-}" \
	twoopstracker.wsgi:application

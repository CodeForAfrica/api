#!/bin/sh
./pex manage migrate --noinput       # Apply database migrations
./pex manage collectstatic --noinput # Collect static files

# Prepare log files and start outputting logs to stdout
touch ./logs/gunicorn.log
touch ./logs/access.log
touch ./logs/celery.log

tail -n 0 -f ./logs/*.log &

# Start celery worker
echo Starting celery worker
./pex celery -A twoopstracker worker -l INFO >/dev/null 2>./logs/celery.log &

# everytime the container is restarted, the scheduler will reset
rm -rf celerybeat-schedule
# Start celery beat service
echo Starting celery beat
./pex celery -A twoopstracker beat -l INFO >/dev/null 2>./logs/celery.log &

# Start Gunicorn processes
echo Starting gunicorn
exec ./pex gunicorn \
	--bind 0.0.0.0:8000 \
	--workers="${TWOOPSTRACKER_GUNICORN_WORKERS:-3}" \
	--worker-class gevent \
	--log-level="${TWOOPSTRACKER_GUNICORN_LOG_LEVEL:-warning}" \
	--timeout="${TWOOPSTRACKER_GUNICORN_TIMEOUT:-60}" \
	--log-file=./logs/gunicorn.log \
	--access-logfile=./logs/access.log \
	--name twoopstracker \
	"${TWOOPSTRACKER_GUNICORN_EXTRA_CONFIG:---reload}" \
	twoopstracker.wsgi:application

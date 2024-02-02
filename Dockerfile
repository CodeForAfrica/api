FROM python:3.9

WORKDIR /app
COPY . /app

RUN pip install virtualenv
ENV PATH="/app/pesacheck_meedan_bridge/venv/bin:$PATH"
RUN virtualenv /app/pesacheck_meedan_bridge/venv
RUN echo "source /app/pesacheck_meedan_bridge/venv/bin/activate" >> ~/.bashrc
RUN pip install --no-cache-dir -r pesacheck_meedan_bridge/requirements.txt

RUN apt-get update && apt-get -y install cron

RUN chmod +x /app/pesacheck_meedan_bridge/service.py
ADD crontab /etc/cron.d/crontab

RUN chmod 0644 /etc/cron.d/crontab

RUN crontab /etc/cron.d/crontab

CMD ["cron", "-f"]


# Використання офіційного образу Python
FROM python:3.9-slim

# Встановлення залежностей
RUN pip install --no-cache-dir faster-whisper \
    flask \
    gunicorn \
    pymongo \
    flask-cors

ADD transcript-cron /etc/cron.d/transcript-cron
RUN chmod 0644 /etc/cron.d/transcript-cron

RUN apt-get update \
    && apt-get install -y cron

# Створення робочої директорії
WORKDIR /app

# Копіювання всього коду до контейнера
COPY . /app

COPY transcript-cron /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

RUN crontab /etc/cron.d/crontab

#COPY transcript-cron /etc/cronjob
#RUN chmod 0644 /etc/cronjob
#RUN crontab /etc/cronjob

RUN touch /var/log/cron.log

RUN cron

# Відкриття порту 5000
EXPOSE 5000

# Запуск Gunicorn сервера
#tail -f /var/log/cron.log &&
#CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "3000", "--bind", "0.0.0.0:5000", "app:app"]
CMD ["bash", "-c", "(cron && gunicorn --workers 4 --threads 8 --timeout 6000 --bind 0.0.0.0:5000 app:app)"]

# Використання офіційного образу Python
FROM python:3.9-slim

# Встановлення залежностей
RUN pip install --no-cache-dir faster-whisper \
    flask \
    gunicorn \
    pymongo

# Створення робочої директорії
WORKDIR /app

# Копіювання всього коду до контейнера
COPY . /app

RUN  sleep 2m

# Відкриття порту 5000
EXPOSE 5000

# Запуск Gunicorn сервера
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "3000", "--bind", "0.0.0.0:5000", "app:app"]

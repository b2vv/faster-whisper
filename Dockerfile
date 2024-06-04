# Використання офіційного образу Python
FROM nvidia/cuda:11.4.2-cudnn8-runtime-ubuntu20.04

# Встановлення Python and other залежностей
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages


# Create working directory
WORKDIR /app

# Copy the application code
COPY . /app

# Встановлення залежностей
RUN pip3 install --no-cache-dir \
    faster-whisper \
    flask \
    flask-cors \
    gunicorn

# Створення робочої директорії
WORKDIR /app

# Копіювання всього коду до контейнера
COPY . /app

RUN  sleep 2m

# Відкриття порту 5000
EXPOSE 5000

# Запуск Gunicorn сервера
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "300", "--bind", "0.0.0.0:5000", "app:app"]

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /bot/code

# Системные зависимости для сборки wheels и работы с Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential libpq5 libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Установим зависимости
COPY ./requirements*.txt ./
RUN python -m pip install --upgrade pip \
 && pip install -r requirements.txt

# Копируем исходники внутрь образа
COPY ./src /bot/code

EXPOSE 8080

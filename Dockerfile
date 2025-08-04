FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./requirements*.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

ADD ./src /bot/code
WORKDIR /bot/code

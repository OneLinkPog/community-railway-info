# Dockerfile for Python 3.13 with uv installed
FROM python:3.13-slim-trixie

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && mv /root/.local/bin/uv /usr/local/bin/uv

EXPOSE 30789

ENV PYTHONUNBUFFERED=1

CMD ["bash"]
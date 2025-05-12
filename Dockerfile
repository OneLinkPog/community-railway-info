FROM debian:testing-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*


RUN pip3 install -r requirements.txt

EXPOSE 30789

ENV PYTHONUNBUFFERED=1

CMD ["python3", "__main__.py"]
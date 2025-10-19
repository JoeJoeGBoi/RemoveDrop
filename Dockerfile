# Minimal, production-friendly build
FROM python:3.11-slim

# Install ffmpeg for video I/O (Telegram & inspection)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .env.example ./
COPY README.md ./

ENV PYTHONUNBUFFERED=1

# Default command: run bot (worker is a separate service in docker-compose)
CMD ["python", "app/bot.py"]

# Telegram Background Remover Bot (Video & GIF) — Production-Ready

This repo gives you a production-grade Telegram bot that removes backgrounds from **MP4s and GIFs** using the open-source [`backgroundremover`](https://github.com/nadermx/backgroundremover) CLI. No external SaaS dependencies required. Includes job queue, worker, Docker, and Docker Compose.

## Features
- Supports MP4 and GIF (Telegram video & animation)
- Uses the **backgroundremover** CLI locally for high-quality matting
- **Job queue** with **Redis + RQ** (decoupled bot and worker)
- File size caps on uploads
- Clean logging, temp file management
- **Dockerfile** and **docker-compose.yml**
- `.env` based configuration

## Quick Start

### 1) Create Telegram Bot
- Talk to `@BotFather`
- Grab `TELEGRAM_BOT_TOKEN` and set it in `.env`

### 2) Configure environment
Copy and edit:
```bash
cp .env.example .env
# edit .env with your token
```

### 3) Start with Docker Compose
```bash
docker compose up --build
```
This brings up:
- `redis`: message broker
- `bot`: Telegram polling bot
- `worker`: background processor that runs the local background removal and sends the result back to the user

### 4) Use it
Send a **GIF** or **MP4** to your bot. It will reply with a processed video (transparent background preserved when possible).

---

## File Structure

```
app/
  bot.py                # Telegram bot (polling), enqueues jobs
  worker.py             # RQ worker that runs the processing job
  handlers.py           # Telegram handlers and validation
  queue.py              # RQ queue setup and job helpers
  config.py             # Settings from env (with sane defaults)
  processing/bgremover_local.py  # backgroundremover CLI wrapper
  utils/logger.py       # Logging helpers
Dockerfile
docker-compose.yml
requirements.txt
.env.example
README.md
```

---

## Notes & Gotchas

- **FFmpeg** is installed in the container for GIF shrinking and general video handling.
- For GIF input, Telegram sends it as `animation`. We normalize flow so both go through the same pipeline.
- **Transparency**: `backgroundremover` outputs videos with alpha (MOV/WebM). Telegram will transcode on upload, so expect MP4 output even though transparency is preserved during processing.
- **First run**: The backgroundremover CLI downloads model weights on first use. Allow a little extra time for the initial job.
- **Privacy**: Everything runs locally in the worker container—no third-party API calls.
- **Scaling**: Add more `worker` replicas. RQ + Redis makes it horizontal.
- **Limits**: You can tune `MAX_FILE_MB` and allowed durations in `.env`.

---

## Environment (.env)

See `.env.example` — required keys:
- `TELEGRAM_BOT_TOKEN`

Optional:
- `REDIS_URL=redis://redis:6379/0`
- `QUEUE_NAME=bgremove`
- `MAX_FILE_MB=50`
- `LOG_LEVEL=INFO`

---

## Manual Run (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export $(grep -v '^#' .env | xargs)  # load env vars in your shell

# Start redis (on Mac: brew services start redis; on Linux: apt install redis-server)
rq worker --url $REDIS_URL $QUEUE_NAME &

python app/bot.py
```

## Healthcheck

- Bot logs at startup: it will show your bot username once connected.
- Run `docker compose logs -f bot worker` to tail both services.

---

## Customising the processor

All of the background removal logic lives in `app/processing/bgremover_local.py`. If you want to swap in a different model or service, replace that module but keep the same interface:
```python
def process_video(input_path: str) -> dict:
    # return { "output_url": "<https url or None>", "meta": {...}, "output_path": "<optional local path>" }
```

Bless the pipeline. Keep it clean, fast, and brutally simple.

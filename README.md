# Telegram Background Remover Bot (Video & GIF) — Production-Ready

This repo gives you a production-grade Telegram bot that removes backgrounds from **MP4s and GIFs** using a **hosted API** (Replicate's Robust Video Matting). No GPUs to manage, just deploy and go. Includes job queue, worker, Docker, and docker-compose.

## Features
- Supports MP4 and GIF (Telegram video & animation)
- Uses **Replicate (RVM)** API for high‑quality matting
- **Job queue** with **Redis + RQ** (decoupled bot and worker)
- **Rate limiting** & file size caps
- Clean logging, temp file management
- **Dockerfile** and **docker-compose.yml**
- `.env` based configuration

## Quick Start

### 1) Create a Replicate account & token
- https://replicate.com
- Set `REPLICATE_API_TOKEN` in `.env`

### 2) Create Telegram Bot
- Talk to `@BotFather`
- Grab `TELEGRAM_BOT_TOKEN` and set it in `.env`

### 3) Configure environment
Copy and edit:
```bash
cp .env.example .env
# edit .env with your tokens
```

### 4) Start with Docker Compose
```bash
docker compose up --build
```
This brings up:
- `redis`: message broker
- `bot`: Telegram polling bot
- `worker`: background processor that calls Replicate and sends the result back to the user

### 5) Use it
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
  processing/replicate_video.py  # Replicate (RVM) client wrapper
  utils/logger.py       # Logging helpers
Dockerfile
docker-compose.yml
requirements.txt
.env.example
README.md
```

---

## Notes & Gotchas

- **FFmpeg** is installed in the container. Replicate returns URLs; Telegram accepts remote URLs for `sendVideo`.
- For GIF input, Telegram sends it as `animation`. We normalize flow so both go through the same pipeline.
- **Transparency**: Many players don't show alpha in MP4. Replicate output may be PNG sequences or video. We forward the returned URL. Telegram transcodes on upload; expect MP4 output.
- **Privacy**: Files are processed by a third‑party API. Disclose this if you have compliance needs.
- **Scaling**: Add more `worker` replicas. RQ + Redis makes it horizontal.
- **Limits**: You can tune `MAX_FILE_MB` and allowed durations in `.env`.

---

## Environment (.env)

See `.env.example` — required keys:
- `TELEGRAM_BOT_TOKEN`
- `REPLICATE_API_TOKEN`

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

## Switching to another API

The `processing/replicate_video.py` is the only place calling Replicate. To swap APIs (e.g., ByteDance Volcano Engine), replace that module but keep the same interface:
```python
def process_video(input_path: str) -> dict:
    # return { "output_url": "<https url>", "meta": {...} }
```

Bless the pipeline. Keep it clean, fast, and brutally simple.


### Backend Options

You can choose the processing backend with `BACKEND` env var:
- `replicate` (default): Hosted Robust Video Matting via Replicate.
- `local`: Uses open‑source **nadermx/backgroundremover** (CLI) locally.

Set in `.env`:
```bash
BACKEND=local   # or replicate
```

Local mode requires the `backgroundremover` package (included in `requirements.txt`) and downloads models on first run.

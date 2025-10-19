import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure repository root is on the path before importing project modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Ensure required environment variables exist before importing config
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app import handlers  # noqa: E402


def run(coro):
    return asyncio.run(coro)


def test_handle_media_rejects_too_large_file():
    oversized_bytes = (handlers.MAX_FILE_MB + 1) * 1024 * 1024

    video = SimpleNamespace(file_size=oversized_bytes, get_file=AsyncMock())
    message = SimpleNamespace(
        video=video,
        animation=None,
        reply_text=AsyncMock(),
        chat_id=123,
    )
    update = SimpleNamespace(message=message)

    run(handlers.handle_media(update, None))

    message.reply_text.assert_awaited()
    args, _ = message.reply_text.await_args
    assert "Max allowed" in args[0]


class _FakeTelegramFile:
    async def download_to_drive(self, destination: str) -> None:
        with open(destination, "wb") as fh:
            fh.write(b"data")


class _FakeVideo:
    def __init__(self, file_size: int):
        self.file_size = file_size

    async def get_file(self):
        return _FakeTelegramFile()


def test_handle_media_enqueues_job():
    video = _FakeVideo(file_size=handlers.MAX_FILE_MB * 1024 * 1024)
    status_message = SimpleNamespace(message_id=777)

    message = SimpleNamespace(
        video=video,
        animation=None,
        reply_text=AsyncMock(return_value=status_message),
        chat_id=42,
    )
    update = SimpleNamespace(message=message)

    enqueue_mock = MagicMock(return_value=SimpleNamespace(id="job-123"))

    with patch.object(handlers.queue, "enqueue", enqueue_mock):
        run(handlers.handle_media(update, None))

    message.reply_text.assert_awaited_once()
    args, kwargs = enqueue_mock.call_args
    function_name, chat_id, status_id, input_path = args
    assert function_name == "app.worker.process_and_reply"
    assert chat_id == 42
    assert status_id == status_message.message_id
    assert kwargs["job_timeout"] == 60 * 20

    reply_args, _ = message.reply_text.await_args
    assert "Got it." in reply_args[0]

    assert os.path.exists(input_path)
    os.remove(input_path)

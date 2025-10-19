import os
import subprocess
import tempfile
from ..utils.logger import get_logger

log = get_logger(__name__)

def _which(cmd: str) -> str | None:
    from shutil import which
    return which(cmd)

def process_video(input_path: str) -> dict:
    """
    Uses the open-source `backgroundremover` CLI (nadermx/backgroundremover) to remove
    background from a video locally. Outputs a MOV with alpha (ProRes/PNG) or WebM with alpha.
    Returns:
      { "output_url": "<file:// path>", "meta": {...}, "output_path": "<local path>" }
    """
    if not _which("backgroundremover"):
        raise RuntimeError("backgroundremover CLI not found. Ensure the package is installed and on PATH.")
    # prefer MOV w/ alpha (Telegram will transcode but accepts upload; size can be big)
    # The CLI supports -tv for transparent video according to docs.
    out_fd, out_path = tempfile.mkstemp(suffix=".mov")
    os.close(out_fd)

    cmd = [
        "backgroundremover",
        "-i", input_path,
        "-tv",
        "-o", out_path,
    ]
    log.info("Running: %s", " ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        log.error("backgroundremover failed: %s", proc.stderr[-1000:])
        raise RuntimeError(f"backgroundremover failed: {proc.stderr.splitlines()[-1] if proc.stderr else 'unknown error'}")

    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError("No output produced by backgroundremover.")

    # We'll return a local path; worker will upload file bytes directly.
    return { "output_url": None, "output_path": out_path, "meta": {"backend": "local/backgroundremover"} }

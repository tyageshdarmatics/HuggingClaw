import os
import sys
import json
import time
import mimetypes
import tempfile
from pathlib import Path

import requests
import fal_client


FAL_MODEL = "fal-ai/bytedance/seedance/v1.5/pro/image-to-video"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def ensure_file_or_url(image_input: str) -> str:
    """
    If image_input is a local path, upload it to fal and return a hosted URL.
    If image_input is already an http(s) URL, return as-is.
    """
    image_input = image_input.strip()

    if image_input.startswith("http://") or image_input.startswith("https://"):
        return image_input

    p = Path(image_input)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Approved image not found: {image_input}")

    uploaded_url = fal_client.upload_file(str(p))
    return uploaded_url


def generate_video(prompt: str, image_url: str) -> str:
    """
    Call fal Seedance 1.5 Pro image-to-video and return the final video URL.
    """
    def on_queue_update(update):
        try:
            logs = getattr(update, "logs", None)
            if logs:
                for log in logs:
                    msg = log.get("message")
                    if msg:
                        print(f"[fal] {msg}", flush=True)
        except Exception:
            pass

    result = fal_client.subscribe(
        FAL_MODEL,
        arguments={
            "prompt": prompt,
            "image_url": image_url,
            "aspect_ratio": "9:16",
            "resolution": "720p",
            "duration": "5",
            "generate_audio": False,
            "enable_safety_checker": True,
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )

    video = result.get("video") or {}
    video_url = video.get("url")
    if not video_url:
        raise RuntimeError(f"fal returned no video URL. Raw response: {json.dumps(result)}")

    return video_url


def download_file(url: str, suffix: str = ".mp4") -> Path:
    """
    Download the generated video locally and return the file path.
    """
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()

    fd, temp_path = tempfile.mkstemp(prefix="unspoken_shorts_", suffix=suffix)
    os.close(fd)

    out_path = Path(temp_path)
    with open(out_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    return out_path


def send_to_telegram(file_path: Path, caption: str = "") -> dict:
    """
    Upload the local MP4 to Telegram as a document/video.
    """
    bot_token = require_env("TELEGRAM_BOT_TOKEN")
    chat_id = require_env("TELEGRAM_CHAT_ID")

    mime_type, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type or "video/mp4"

    # sendVideo is better if Telegram can preview it
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"

    with open(file_path, "rb") as f:
        files = {
            "video": (file_path.name, f, mime_type)
        }
        data = {
            "chat_id": chat_id,
            "caption": caption[:1024] if caption else ""
        }
        response = requests.post(url, data=data, files=files, timeout=300)

    # Fallback to sendDocument if needed
    if response.status_code >= 400:
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(file_path, "rb") as f:
            files = {
                "document": (file_path.name, f, "video/mp4")
            }
            data = {
                "chat_id": chat_id,
                "caption": caption[:1024] if caption else ""
            }
            response = requests.post(url, data=data, files=files, timeout=300)

    response.raise_for_status()
    return response.json()


def main():
    """
    Usage:
      python run_unspoken_shorts.py "<image_path_or_url>" "<video_prompt>"
    """
    require_env("FAL_KEY")
    require_env("TELEGRAM_BOT_TOKEN")
    require_env("TELEGRAM_CHAT_ID")

    if len(sys.argv) < 3:
        print(
            "Usage: python run_unspoken_shorts.py \"<image_path_or_url>\" \"<video_prompt>\"",
            file=sys.stderr,
        )
        sys.exit(1)

    image_input = sys.argv[1]
    video_prompt = sys.argv[2]

    try:
        print("[step] Preparing approved image...", flush=True)
        image_url = ensure_file_or_url(image_input)
        print(f"[ok] Image ready: {image_url}", flush=True)

        print("[step] Generating Seedance video...", flush=True)
        video_url = generate_video(video_prompt, image_url)
        print(f"[ok] Video URL received from fal", flush=True)

        print("[step] Downloading video...", flush=True)
        local_video = download_file(video_url, ".mp4")
        print(f"[ok] Downloaded: {local_video}", flush=True)

        print("[step] Uploading to Telegram...", flush=True)
        tg = send_to_telegram(local_video, caption="Unspoken-Shorts result")
        print("[ok] Telegram upload complete", flush=True)

        print(json.dumps({
            "status": "success",
            "video_url": video_url,
            "local_file": str(local_video),
            "telegram_result": tg
        }, indent=2))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
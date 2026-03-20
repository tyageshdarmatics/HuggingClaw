import os
import sys
import json
import time
import mimetypes
import tempfile
import urllib.parse
from pathlib import Path
import shutil
import subprocess

import requests
import fal_client

FAL_MODEL = "fal-ai/bytedance/seedance/v1.5/pro/image-to-video"

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def download_image_pollinations(prompt: str, out_path: Path):
    """
    Download a free 9:16 image from pollinations.ai
    """
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1365&nologo=true"
    
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()
    
    with open(out_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"[ok] Downloaded Image to {out_path}")
    return out_path

def ensure_file_or_url(image_input: str) -> str:
    image_input = image_input.strip()
    if image_input.startswith("http://") or image_input.startswith("https://"):
        return image_input
    p = Path(image_input)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Image not found: {image_input}")
    print(f"[step] Uploading {image_input} to fal...", flush=True)
    uploaded_url = fal_client.upload_file(str(p))
    return uploaded_url

def generate_video(prompt: str, image_url: str, end_image_url: str = None) -> str:
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
            
    arguments = {
        "prompt": prompt,
        "image_url": image_url,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        "duration": "5",
        "generate_audio": True,
        "enable_safety_checker": True,
    }
    # Pass end_image_url in case the model supports it natively
    if end_image_url:
        arguments["end_image_url"] = end_image_url

    result = fal_client.subscribe(
        FAL_MODEL,
        arguments=arguments,
        with_logs=True,
        on_queue_update=on_queue_update,
    )

    video = result.get("video") or {}
    video_url = video.get("url")
    if not video_url:
        raise RuntimeError(f"fal returned no video URL. Raw response: {json.dumps(result)}")

    return video_url

def download_file(url: str, out_path: Path):
    print(f"[step] Downloading video to {out_path}...", flush=True)
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()

    with open(out_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
    print(f"[ok] Downloaded video: {out_path}")
    return out_path

def stitch_videos(video_paths: list, output_path: Path):
    print("[step] Stitching videos with ffmpeg...", flush=True)
    list_file_path = output_path.parent / "files_to_stitch.txt"
    with open(list_file_path, "w", encoding="utf-8") as f:
        for p in video_paths:
            # Need to escape backslashes for ffmpeg on windows if using single quotes, but cleaner to just replace
            clean_path = str(p.absolute()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")
    
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file_path.absolute()), "-c", "copy",
        str(output_path.absolute())
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[ok] Successfully stitched into {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"[error] ffmpeg failed! Stderr: {e.stderr.decode('utf-8', errors='ignore')}")
        raise RuntimeError("Failed to stitch videos with ffmpeg.")
    finally:
        if list_file_path.exists():
            list_file_path.unlink()

def send_to_telegram(file_path: Path, caption: str = "") -> dict:
    bot_token = require_env("TELEGRAM_BOT_TOKEN")
    chat_id = require_env("TELEGRAM_CHAT_ID")
    mime_type, _ = mimetypes.guess_type(str(file_path))
    mime_type = mime_type or "video/mp4"

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    with open(file_path, "rb") as f:
        files = {"video": (file_path.name, f, mime_type)}
        data = {"chat_id": chat_id, "caption": caption[:1024] if caption else ""}
        response = requests.post(url, data=data, files=files, timeout=300)

    if response.status_code >= 400:
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(file_path, "rb") as f:
            files = {"document": (file_path.name, f, "video/mp4")}
            data = {"chat_id": chat_id, "caption": caption[:1024] if caption else ""}
            response = requests.post(url, data=data, files=files, timeout=300)

    response.raise_for_status()
    return response.json()

def main():
    require_env("FAL_KEY")
    require_env("TELEGRAM_BOT_TOKEN")
    require_env("TELEGRAM_CHAT_ID")

    if len(sys.argv) < 2:
        print("Usage: python generate_cinematic_pipeline.py <scenes_json_path>", file=sys.stderr)
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Error: JSON file not found at {json_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    original_prompt = data.get("original_prompt", "Cinematic Video")
    scenes = data.get("scenes", [])
    if len(scenes) != 4:
        print(f"Error: Required exactly 4 scenes, found {len(scenes)}", file=sys.stderr)
        sys.exit(1)

    base_dir = Path(__file__).parent.resolve()
    img_dir = base_dir / "generated_images"
    vid_dir = base_dir / "generated_videos"
    img_dir.mkdir(parents=True, exist_ok=True)
    vid_dir.mkdir(parents=True, exist_ok=True)

    local_images = []
    fal_image_urls = []
    local_videos = []

    try:
        # 1. Generate 4 local images via Pollinations (Free)
        print("[step] Generating 4 Images with Pollinations.ai (Free)...")
        for i, scene in enumerate(scenes, 1):
            p = scene.get("prompt", "cinematic scene")
            out_img = img_dir / f"scene_{i}.jpg"
            download_image_pollinations(p, out_img)
            local_images.append(out_img)

        # 2. Upload images to Fal to get URLs for Video Gen
        print("[step] Uploading Images to Fal...")
        for img_path in local_images:
            url = ensure_file_or_url(str(img_path))
            fal_image_urls.append(url)

        # 3. Generate 3 Videos using Seedance 1.5 Pro
        print("[step] Generating 3 Video Clips via Fal AI Seedance...")
        for i in range(3):
            print(f"--- Generating Clip {i+1}/3 ---", flush=True)
            clip_prompt = original_prompt  # Or combine with scene prompts
            start_url = fal_image_urls[i]
            end_url = fal_image_urls[i+1]
            
            vid_url = generate_video(clip_prompt, start_url, end_url)
            out_vid = vid_dir / f"clip_{i+1}.mp4"
            download_file(vid_url, out_vid)
            local_videos.append(out_vid)

        # 4. Stitch 3 Clips
        print("[step] Commencing Video Stitch...")
        final_video = vid_dir / "final_cinematic.mp4"
        stitch_videos(local_videos, final_video)

        # 5. Send to Telegram
        print("[step] Uploading to Telegram...")
        caption = "Video generated successfully 😀\n\nPrompt: " + original_prompt
        send_to_telegram(final_video, caption=caption)
        print("\n\nSUCCESS! Video sent to Telegram.")
        
    except Exception as e:
        print(f"\nERROR: Pipeline Failed -> {e}", file=sys.stderr)
        sys.exit(2)
        
    finally:
        # Auto-delete
        print("[cleanup] Scheduling local artifacts deletion...")
        try:
            if img_dir.exists():
                shutil.rmtree(img_dir)
            if vid_dir.exists():
                shutil.rmtree(vid_dir)
            print("[cleanup] Done.")
        except Exception as e:
            print(f"[cleanup] Warning: failed to delete temp dirs: {e}")

if __name__ == "__main__":
    main()

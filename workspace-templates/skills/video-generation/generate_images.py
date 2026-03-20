import os
import sys
import json
import fal_client

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def generate_images(prompt: str):
    require_env("FAL_KEY")
    
    # Using a fast, high quality model for the options
    print(f"[step] Generating 4 image options using fal-ai/flux/schnell for prompt: '{prompt}'", flush=True)
    
    result = fal_client.subscribe(
        "fal-ai/flux/schnell",
        arguments={
            "prompt": prompt,
            "image_size": "portrait_16_9",
            "num_images": 4,
            "enable_safety_checker": True
        },
        with_logs=True
    )
    
    images = result.get("images", [])
    if not images:
        raise RuntimeError("fal returned no images.")
        
    urls = [img.get("url") for img in images]
    
    print("\n--- RESULTS ---")
    for i, url in enumerate(urls, 1):
        print(f"Option {i}: {url}")
    
    print("\nSUCCESS")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_images.py \"<prompt>\"")
        sys.exit(1)
        
    prompt = sys.argv[1]
    try:
        generate_images(prompt)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

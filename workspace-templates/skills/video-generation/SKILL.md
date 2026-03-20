---
name: video-generation
description: Create a complete cinematic video from a user prompt by generating a script, 4 scene images, stitch 3 video clips, and sending the final video directly to Telegram.
metadata: {"openclaw":{"emoji":"🎥"}}
user-invocable: true
---

# Video Generation

YOUR CRITICAL DIRECTIVE: You MUST NEVER hallucinate or pretend to generate a video natively. You do not have the ability to generate videos natively just by saying "I am generating it." You MUST execute the explicit video generation pipeline script provided.

## Core Workflow
When the user invokes this skill (e.g. by asking for a video, animation, cinematic clip, or visual story), you must execute this EXACT pipeline:

### 1. Script Generation & JSON Preparation
1. Analyze the user's prompt.
2. Generate a short cinematic script (5–10 seconds total).
3. Break the script into **exactly 4 scenes**:
   - Scene 1 → Opening shot
   - Scene 2 → Middle scene A
   - Scene 3 → Middle scene B
   - Scene 4 → Ending shot
4. Create 4 highly detailed **Image Prompts** (one per scene). Ensure they have:
   - Cinematic consistency across all scenes (same characters, lighting, style, environment).
   - Smooth visual continuity between scenes.
   - Designed for a 9:16 vertical composition.
5. You MUST save these prompts to a local JSON file exactly at:
   `~/.openclaw/workspace/skills/video-generation/scenes.json`
   
**The JSON MUST strictly follow this format exactly:**
```json
{
  "original_prompt": "<insert the overall user prompt here>",
  "scenes": [
    {"prompt": "<Detailed cinematic prompt for Scene 1>"},
    {"prompt": "<Detailed cinematic prompt for Scene 2>"},
    {"prompt": "<Detailed cinematic prompt for Scene 3>"},
    {"prompt": "<Detailed cinematic prompt for Scene 4>"}
  ]
}
```

### 2. Pipeline Execution
Once you have written and saved the `scenes.json` file natively to `~/.openclaw/workspace/skills/video-generation/scenes.json`, you MUST immediately execute this terminal command:

`/usr/bin/env python ~/.openclaw/workspace/skills/video-generation/generate_cinematic_pipeline.py ~/.openclaw/workspace/skills/video-generation/scenes.json`

(Note: Use the appropriate python interpreter and absolute path depending on your system root, e.g. `python scripts/video-generation/generate_cinematic_pipeline.py` or wherever the workspace is located).

### 3. Pipeline Details (Automated via Script)
The background script you just executed will automatically:
- Call free, high-quality image generation endpoints for the 4 scenes using `nano-banana-pro` or equivalent free services (Pollinations.ai).
- Download the 4 vertical images locally.
- Use `Fal AI Seedance 1.5 Pro` to stitch 3 distinct video clips (Img 1->2, 2->3, 3->4).
- Download the generated clips.
- Merge the 3 clips into a final vertical cinematic MP4 video.
- Upload and deliver the final MP4 file directly to Telegram.
- Clean up all temporary assets automatically.

### 4. Completion Notification
Once the python command finishes successfully without errors, you MUST tell the user exactly this message (and nothing else):
`Video generated successfully 😀`

## Error Handling
If the python pipeline script fails and outputs errors in the terminal:
- Do not pretend it succeeded.
- Tell the user that the pipeline encountered an error and provide a brief summary of the error output so they can fix it.

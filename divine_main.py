import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STORY_ID = os.getenv("STORY_ID", "krishna-vichaar")
STORY_FILE = ROOT / "stories" / STORY_ID / "story.json"
OUT = ROOT / "output"
WORK = ROOT / "work"
TOOLS = ROOT / "tools"

OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)


def flatten_story(story):
    scenes = []
    for chapter in story.get("chapters", []):
        chapter_title = chapter.get("title", "विचार")
        for segment in chapter.get("segments", []):
            scenes.append({
                "id": segment.get("id", ""),
                "chapter": chapter_title,
                "title": segment.get("title", chapter_title),
                "text": " ".join(segment.get("narration", "").split()),
                "narration": segment.get("narration", ""),
                "visual_path": segment.get("visual", ""),
                "motion": segment.get("motion", "slow_push_in"),
                "label": segment.get("label", "विचार"),
            })
    if not scenes:
        raise ValueError("story.json contains no segments.")
    return scenes


def load_story():
    if not STORY_FILE.exists():
        raise FileNotFoundError(f"Story not found: {STORY_FILE}")
    data = json.loads(STORY_FILE.read_text(encoding="utf-8-sig"))
    if "chapters" not in data:
        raise ValueError("story.json must contain chapters[].")
    return data, flatten_story(data)


def make_manifest(story, scenes):
    return {
        "story_id": STORY_ID,
        "title": story.get("title", STORY_ID),
        "subtitle": story.get("subtitle", ""),
        "format": story.get("format", "devotional_short"),
        "aspect_ratio": story.get("aspect_ratio", "9:16"),
        "scenes": [{**scene, "number": i + 1} for i, scene in enumerate(scenes)],
        "ending": story.get("ending", {}),
        "tts": {
            "provider": os.getenv("TTS_PROVIDER", "aws_polly"),
            "enabled": os.getenv("TTS_ENABLED", "false").lower() == "true",
        },
    }


def run():
    story, scenes = load_story()
    manifest = make_manifest(story, scenes)
    manifest_path = WORK / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    silent = WORK / "silent.mp4"
    renderer = TOOLS / "render_bhagwan.js"

    subprocess.run(
        ["node", str(renderer), str(manifest_path), str(silent)],
        check=True,
    )

    tts_enabled = manifest["tts"]["enabled"]
    if not tts_enabled:
        final = OUT / "divine-vichaar-visual-test.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(silent),
            "-c:v", "copy", "-an", "-movflags", "+faststart", str(final)
        ], check=True)
        print(f"VIDEO READY (visual-only): {final}")
        print("TTS provider configured:", manifest["tts"]["provider"])
        print("TTS was NOT called.")
        return

    # Provider-independent hook. The selected provider writes WORK/narration.mp3.
    tts_script = TOOLS / "tts.py"
    subprocess.run(
        ["python", str(tts_script), str(manifest_path), str(WORK / "narration.mp3")],
        check=True,
    )

    final = OUT / "divine-vichaar.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(silent),
        "-i", str(WORK / "narration.mp3"),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", str(final)
    ], check=True)
    print(f"VIDEO READY: {final}")


if __name__ == "__main__":
    run()

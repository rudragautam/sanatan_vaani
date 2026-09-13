import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("Usage: validate_story.py <story.json>")

p = Path(sys.argv[1])
data = json.loads(p.read_text(encoding="utf-8-sig"))

assert data.get("chapters"), "chapters[] is required"
count = 0
for chapter in data["chapters"]:
    assert chapter.get("title"), "chapter.title is required"
    for segment in chapter.get("segments", []):
        for field in ("id", "title", "narration", "visual"):
            assert segment.get(field), f"segment.{field} is required"
        visual = Path(segment["visual"])
        assert (Path(__file__).resolve().parents[1] / visual).exists(), f"missing visual: {visual}"
        count += 1

assert count > 0, "no segments found"
print(f"OK — validated {count} segments.")

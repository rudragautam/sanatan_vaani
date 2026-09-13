import os
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: tts.py <manifest.json> <output.mp3>")

    provider = os.getenv("TTS_PROVIDER", "aws_polly").lower()
    output = Path(sys.argv[2])

    if provider == "aws_polly":
        if os.getenv("TTS_ENABLED", "false").lower() != "true":
            raise SystemExit("AWS Polly is disabled. Set TTS_ENABLED=true to call Polly.")
        raise SystemExit(
            "AWS Polly adapter is intentionally gated here for the visual test. "
            "Implement the provider call in this adapter when TTS is enabled."
        )

    raise SystemExit(f"Unsupported TTS provider: {provider}")

if __name__ == "__main__":
    main()

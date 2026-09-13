# DivineVaani

Reference implementation for a reusable devotional-video automation niche.

## Pipeline

`story.json`
→ Python manifest
→ HTML template + injected data
→ Playwright/Chromium frame capture
→ FFmpeg video
→ optional TTS provider
→ final MP4

## Design contract

`templates/bhagwan_vichaar.html` is the supplied HTML presentation template.
The pipeline treats HTML/CSS as the visual system and does not replace it with
an SVG/canvas/second visual design.

## Visual test

The GitHub Actions workflow runs with:

- `TTS_ENABLED=false`
- `TTS_PROVIDER=aws_polly`

Therefore the visual test does not call AWS Polly.

## TTS

TTS is a provider stage. The adapter currently gates AWS Polly behind
`TTS_ENABLED=true`. The visual test deliberately does not call it.

## Content

Add each episode under `stories/<content-id>/story.json` and keep visuals
under `visuals/`. Python orchestration does not hardcode story copy.

# Local Pipeline

This skill is fully local and does not call online model APIs.

## Render pipeline

1. Prompt -> generate deterministic SVG (Python script)
2. SVG -> PNG via local renderer

Renderer priority:

1. `rsvg-convert`
2. `inkscape`
3. macOS `sips`
4. `magick` (ImageMagick)

If none are available, install one renderer and rerun.

## Notes

- No API key required.
- Output is reproducible for the same prompt and size.
- Supports OpenClaw asset generation: `thumbnail/icon` as both `.svg` and `.png`.

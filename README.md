# Free ImageGen Skill

`Free ImageGen` is a fully local text-to-image skill that turns prompts into SVG artwork and exports PNG output without calling any online model APIs.

It is designed for Codex-style workflows, OpenClaw asset generation, and quick visual prototyping when you want editable vector output plus a ready-to-use raster image.

## What It Does

- Generates images from a natural-language prompt
- Uses a local `Prompt -> SVG -> PNG` pipeline
- Defaults to general illustration mode for characters, objects, and scenes
- Switches to cover mode only when the prompt explicitly asks for `cover`, `thumbnail`, `poster`, `banner`, `海报`, or `封面`
- Can generate OpenClaw-ready `thumbnail` and `icon` assets and update `manifest.json`

## Why This Repo Exists

This skill was built to keep image generation lightweight, editable, and free to run locally.

Instead of relying on hosted image APIs, it:

1. interprets the prompt
2. builds SVG composition locally
3. exports PNG through local macOS / desktop renderers

That makes it useful for:

- OpenClaw app listing assets
- simple promotional covers
- character and scene mockups
- fast visual experiments where editable SVG matters

## Project Structure

```text
SKILL.md
agents/openai.yaml
references/providers.md
scripts/free_image_gen.py
scripts/free_image_http_service.py
```

## Requirements

The core generator is Python-only, but PNG export needs a local SVG renderer.

Supported renderers, in priority order:

1. `rsvg-convert`
2. `inkscape`
3. `qlmanage`
4. `sips`
5. `magick`

On macOS, `qlmanage` is usually the most reliable fallback.

## Usage

### Generate a normal illustration

```bash
python3 scripts/free_image_gen.py \
  --prompt "长发可爱女生，清新梦幻插画风，柔和光影，细节丰富" \
  --output /absolute/path/output/cute-girl.png \
  --svg-output /absolute/path/output/cute-girl.svg \
  --width 1024 \
  --height 1280
```

### Generate a cover or poster

```bash
python3 scripts/free_image_gen.py \
  --prompt "星际战舰封面海报，三大关卡，巨型Boss，手机也爽玩" \
  --output /absolute/path/output/starship-cover.png \
  --svg-output /absolute/path/output/starship-cover.svg \
  --width 1024 \
  --height 576
```

### Generate OpenClaw assets

```bash
python3 scripts/free_image_gen.py \
  --prompt "space heist arcade lobster game" \
  --openclaw-project /absolute/path/to/your-openclaw-app
```

This writes:

- `assets/thumbnail.svg`
- `assets/thumbnail.png`
- `assets/icon.svg`
- `assets/icon.png`

And updates `manifest.json` if present.

## HTTP Service

Start the local HTTP wrapper:

```bash
python3 scripts/free_image_http_service.py --host 127.0.0.1 --port 8787
```

Health check:

```bash
curl http://127.0.0.1:8787/health
```

Generate one image:

```bash
curl -X POST http://127.0.0.1:8787/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "长发可爱女生，清新梦幻插画风，柔和光影，细节丰富",
    "width": 1024,
    "height": 1280,
    "output": "/absolute/path/output/cute-girl.png",
    "svg_output": "/absolute/path/output/cute-girl.svg"
  }'
```

Generate OpenClaw assets:

```bash
curl -X POST http://127.0.0.1:8787/openclaw-assets \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "space lobster game cover",
    "project": "/absolute/path/to/openclaw-project"
  }'
```

## Prompt Tips

- For illustrations, describe the subject, mood, color palette, and detail level
- For covers, explicitly say `cover`, `thumbnail`, `poster`, `海报`, or `封面`
- If you want text in the image, include it directly in the prompt, for example:
  - `左上角写 NimaTech`
  - `底部大标题 十三香小龙虾`

## Current Limitations

- This is not a photorealistic model-backed generator
- The SVG compositions are rule-based and stylized
- Different prompt categories are handled with handcrafted composition logic
- Output quality depends partly on the local SVG renderer available on the machine

## License

No license file has been added yet. Add one if you want the repository to be reusable by others under explicit terms.

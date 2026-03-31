# Free ImageGen Skill

`Free ImageGen` is a fully local text-to-image skill that turns prompts into SVG artwork and exports PNG output without calling any online model APIs.

It is designed for Codex-style workflows, OpenClaw asset generation, and quick visual prototyping when you want editable vector output plus a ready-to-use raster image.

## What It Does

- Generates images from a natural-language prompt
- Uses a local `Prompt -> SVG -> PNG` pipeline
- Defaults to general illustration mode for characters, objects, and scenes
- Supports infographic mode for structured, text-heavy visuals
- Supports text-cover mode for title-led cover artwork
- Supports article-to-story mode for turning long-form text into a small image set
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
- article-to-image card sets for OpenClaw content workflows
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

### Generate an infographic

```bash
python3 scripts/free_image_gen.py \
  --prompt "AI 编码工作流信息图，标题 GPT-5.4 Coding Workflow，副标题 从需求到提交，核心数字 4，1. 需求理解 2. 代码实现 3. 验证测试 4. 提交发布" \
  --output /absolute/path/output/workflow-infographic.png \
  --svg-output /absolute/path/output/workflow-infographic.svg \
  --width 1080 \
  --height 1440
```

### Generate a text-first cover

```bash
python3 scripts/free_image_gen.py \
  --prompt "文字封面，标题 AI 产品设计原则，副标题 清晰层级 高信息密度 强识别度，核心数字 07" \
  --output /absolute/path/output/text-cover.png \
  --svg-output /absolute/path/output/text-cover.svg \
  --width 1080 \
  --height 1440
```

### Turn an article into a card set

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --story-strategy dense \
  --width 1080 \
  --height 1440
```

This writes a small image sequence such as:

- `01-cover.png/svg`
- `02-*.png/svg`
- `03-*.png/svg`
- `04-*.png/svg`

The generator will try to infer:

- a cover/title card
- official-announcement cards
- data cards
- why/how explanation cards

It also writes:

- `analysis.json` with extracted sections, numbers, and recommended strategy
- `outline.md` with a readable card-by-card outline for the generated image set
- `prompts/*.md` with one saved prompt per generated card

Available story strategies:

- `auto`
- `story`
- `dense`
- `visual`

### Generate outline and prompt files only

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --prompts-only
```

### Generate images from the article workflow

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --images-only
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
- For infographics, include title, subtitle, highlighted number, and bullet points directly in the prompt
- For long-form article conversion, feed plain text after stripping original embedded images
- Preserve headings, lists, tables, and key numbers when preparing article text
- Use `--story-strategy dense` for knowledge-heavy articles
- Use `--story-strategy story` for personal narratives or experience posts
- Use `--story-strategy visual` when the text should stay lighter and more cover-like
- For text-first covers, explicitly say `文字封面`, `text cover`, or `title card`
- For covers, explicitly say `cover`, `thumbnail`, `poster`, `海报`, or `封面`
- If you want text in the image, include it directly in the prompt, for example:
  - `左上角写 NimaTech`
  - `底部大标题 十三香小龙虾`

## Current Limitations

- This is not a photorealistic model-backed generator
- The SVG compositions are rule-based and stylized
- Different prompt categories are handled with handcrafted composition logic
- Article summarization is heuristic and works best on clearly structured writing
- Output quality depends partly on the local SVG renderer available on the machine

## License

No license file has been added yet. Add one if you want the repository to be reusable by others under explicit terms.

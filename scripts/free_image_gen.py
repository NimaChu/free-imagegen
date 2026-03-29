#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPORT_FALLBACK_SCRIPT = Path("/Users/chunima/.codex/skills/svg-png-cover-generator/scripts/export_svg_to_png.sh")


def _slugify(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return normalized or "image"


def _stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def _is_cover_prompt(prompt: str) -> bool:
    lower = prompt.lower()
    keys = ["cover", "thumbnail", "poster", "banner", "海报", "封面", "宣传图", "主视觉"]
    return any(k in lower for k in keys)


def _pick_palette(prompt: str) -> dict[str, str]:
    lower = prompt.lower()
    if any(k in lower for k in ["space", "starship", "galaxy", "boss", "战舰", "深空", "星际"]):
        return {
            "bg_a": "#04162D",
            "bg_b": "#2C2357",
            "fg": "#EAF2FF",
            "muted": "#BFD3F9",
            "accent": "#68E1FF",
            "hot": "#FFB347",
        }
    if any(k in lower for k in ["girl", "cute", "女生", "少女", "可爱", "long hair", "长发"]):
        return {
            "bg_a": "#FFE6F2",
            "bg_b": "#E1F0FF",
            "fg": "#2A2340",
            "muted": "#6F6A8A",
            "accent": "#FF86B3",
            "hot": "#7BD8FF",
        }
    if any(k in lower for k in ["lobster", "龙虾", "十三香"]):
        return {
            "bg_a": "#2B0F18",
            "bg_b": "#6E1F2C",
            "fg": "#FFF1E8",
            "muted": "#FFD1B0",
            "accent": "#FF2B2B",
            "hot": "#FFC857",
        }
    return {
        "bg_a": "#10213F",
        "bg_b": "#3A245A",
        "fg": "#F8FAFC",
        "muted": "#D0D8E9",
        "accent": "#7EE0FF",
        "hot": "#FFB347",
    }


def _extract_text_intent(prompt: str) -> list[tuple[str, str]]:
    intents: list[tuple[str, str]] = []
    patterns = [
        (r"(?:左上角|左上)\s*(?:写|放|加)?\s*[\"“]?([^\"”\n,，。]+)", "top_left"),
        (r"(?:底部大标题|底座大标题|底部标题)\s*(?:写|放|加)?\s*[\"“]?([^\"”\n]+)", "bottom"),
    ]
    for pat, pos in patterns:
        m = re.search(pat, prompt, flags=re.IGNORECASE)
        if m:
            value = m.group(1).strip().strip('"“”')
            if value:
                intents.append((pos, value))
    return intents


def _draw_particles(width: int, height: int, seed: int, color: str, count: int = 36) -> str:
    out: list[str] = []
    for i in range(count):
        x = width * (0.04 + ((_stable_int(f"{seed}-x-{i}") % 9200) / 10000.0) * 0.92)
        y = height * (0.04 + ((_stable_int(f"{seed}-y-{i}") % 9200) / 10000.0) * 0.92)
        r = width * (0.001 + ((_stable_int(f"{seed}-r-{i}") % 10) / 10000.0))
        op = 0.25 + ((_stable_int(f"{seed}-o-{i}") % 70) / 100.0)
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{color}" opacity="{min(op, 0.9):.2f}"/>')
    return "\n    ".join(out)


def _compose_cover_svg(prompt: str, width: int, height: int) -> str:
    palette = _pick_palette(prompt)
    title = "创意封面"
    subtitle = "轻量生成 • 本地渲染 • 风格可变"
    lower = prompt.lower()
    if any(k in lower for k in ["starship", "战舰", "深空", "星际"]):
        title = "星际战舰深空突围"
        subtitle = "三大关卡 • 巨型Boss • 手机也爽玩"
    elif any(k in lower for k in ["lobster", "龙虾"]):
        title = "十三香小龙虾"
        subtitle = "麻辣鲜香 • 爆汁口感 • 夜宵王牌"

    particles = _draw_particles(width, height, _stable_int(prompt), palette["fg"], count=42)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{palette['bg_a']}"/>
      <stop offset="100%" stop-color="{palette['bg_b']}"/>
    </linearGradient>
    <radialGradient id="g1" gradientUnits="userSpaceOnUse" cx="{width*0.22:.2f}" cy="{height*0.65:.2f}" r="{max(width, height)*0.48:.2f}">
      <stop offset="0%" stop-color="{palette['accent']}" stop-opacity="0.26"/>
      <stop offset="100%" stop-color="{palette['accent']}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="g2" gradientUnits="userSpaceOnUse" cx="{width*0.80:.2f}" cy="{height*0.25:.2f}" r="{max(width, height)*0.45:.2f}">
      <stop offset="0%" stop-color="#D2D9FF" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="#D2D9FF" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="100%" height="100%" fill="url(#bg)"/>
  <rect width="100%" height="100%" fill="url(#g1)"/>
  <rect width="100%" height="100%" fill="url(#g2)"/>
  <g>{particles}</g>

  <g opacity="0.95">
    <circle cx="{width*0.76:.2f}" cy="{height*0.40:.2f}" r="{width*0.16:.2f}" fill="#6FAFFF" opacity="0.82"/>
    <circle cx="{width*0.68:.2f}" cy="{height*0.50:.2f}" r="{width*0.18:.2f}" fill="none" stroke="#DEE6FF" stroke-width="{width*0.004:.2f}" opacity="0.8"/>
    <circle cx="{width*0.68:.2f}" cy="{height*0.50:.2f}" r="{width*0.13:.2f}" fill="none" stroke="#AFC5F2" stroke-width="{width*0.002:.2f}" opacity="0.4"/>
    <circle cx="{width*0.68:.2f}" cy="{height*0.58:.2f}" r="{width*0.06:.2f}" fill="{palette['hot']}"/>
    <path d="M {width*0.47:.2f} {height*0.88:.2f} Q {width*0.58:.2f} {height*0.75:.2f} {width*0.68:.2f} {height*0.61:.2f}" stroke="#FF9C7A" stroke-width="{width*0.010:.2f}" fill="none" stroke-linecap="round"/>
    <path d="M {width*0.57:.2f} {height*0.46:.2f} Q {width*0.70:.2f} {height*0.33:.2f} {width*0.83:.2f} {height*0.54:.2f}" stroke="{palette['hot']}" stroke-width="{width*0.008:.2f}" fill="none" stroke-linecap="round"/>
  </g>

  <text x="{width*0.06:.2f}" y="{height*0.12:.2f}" font-family="Avenir Next, Helvetica, Arial, sans-serif" font-size="{max(14, int(width*0.022))}" font-weight="700" letter-spacing="3" fill="{palette['muted']}">CREATIVE VISUAL</text>
  <text x="{width*0.06:.2f}" y="{height*0.34:.2f}" font-family="PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{max(44, int(width*0.08))}" font-weight="900" fill="{palette['fg']}">{html.escape(title)}</text>
  <text x="{width*0.06:.2f}" y="{height*0.50:.2f}" font-family="PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{max(20, int(width*0.034))}" font-weight="700" fill="{palette['muted']}">{html.escape(subtitle)}</text>
</svg>'''


def _compose_illustration_svg(prompt: str, width: int, height: int) -> str:
    palette = _pick_palette(prompt)
    seed = _stable_int(prompt)
    lower = prompt.lower()
    intents = _extract_text_intent(prompt)
    particles = _draw_particles(width, height, seed, palette["fg"], count=28)

    # General composition blocks
    deco: list[str] = []
    for i in range(6):
        x = width * (0.12 + (i * 0.14) % 0.76)
        y = height * (0.18 + ((i * 37) % 100) / 180.0)
        r = width * (0.035 + (i % 3) * 0.01)
        deco.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{palette["hot"]}" opacity="{0.08 + 0.05*(i%4):.2f}"/>')

    subject = "girl" if any(k in lower for k in ["girl", "女生", "少女", "可爱", "long hair", "长发"]) else "abstract"

    if subject == "girl":
        cx = width * 0.52
        cy = height * 0.54
        s = min(width, height)
        body = f'''
        <g>
          <ellipse cx="{cx:.2f}" cy="{cy+s*0.10:.2f}" rx="{s*0.16:.2f}" ry="{s*0.18:.2f}" fill="#F7D4C8" opacity="0.95"/>
          <ellipse cx="{cx-s*0.16:.2f}" cy="{cy+s*0.03:.2f}" rx="{s*0.10:.2f}" ry="{s*0.15:.2f}" fill="#5A3D58" opacity="0.95"/>
          <ellipse cx="{cx+s*0.16:.2f}" cy="{cy+s*0.03:.2f}" rx="{s*0.10:.2f}" ry="{s*0.15:.2f}" fill="#5A3D58" opacity="0.95"/>
          <circle cx="{cx:.2f}" cy="{cy-s*0.02:.2f}" r="{s*0.14:.2f}" fill="#FCE1D6"/>
          <path d="M {cx-s*0.15:.2f} {cy-s*0.08:.2f} Q {cx:.2f} {cy-s*0.26:.2f} {cx+s*0.15:.2f} {cy-s*0.08:.2f} Q {cx+s*0.12:.2f} {cy+s*0.03:.2f} {cx-s*0.12:.2f} {cy+s*0.03:.2f} Z" fill="#4D3449"/>
          <circle cx="{cx-s*0.045:.2f}" cy="{cy-s*0.03:.2f}" r="{s*0.008:.2f}" fill="#2A1E2E"/>
          <circle cx="{cx+s*0.045:.2f}" cy="{cy-s*0.03:.2f}" r="{s*0.008:.2f}" fill="#2A1E2E"/>
          <path d="M {cx-s*0.03:.2f} {cy+s*0.03:.2f} Q {cx:.2f} {cy+s*0.05:.2f} {cx+s*0.03:.2f} {cy+s*0.03:.2f}" stroke="#E287A2" stroke-width="{s*0.006:.2f}" fill="none" stroke-linecap="round"/>
          <circle cx="{cx-s*0.08:.2f}" cy="{cy+s*0.00:.2f}" r="{s*0.015:.2f}" fill="#FFB2C7" opacity="0.45"/>
          <circle cx="{cx+s*0.08:.2f}" cy="{cy+s*0.00:.2f}" r="{s*0.015:.2f}" fill="#FFB2C7" opacity="0.45"/>
        </g>
        '''
    else:
        cx = width * 0.52
        cy = height * 0.55
        s = min(width, height)
        body = f'''
        <g>
          <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{s*0.16:.2f}" fill="{palette['accent']}" opacity="0.85"/>
          <circle cx="{cx+s*0.08:.2f}" cy="{cy-s*0.05:.2f}" r="{s*0.10:.2f}" fill="{palette['hot']}" opacity="0.75"/>
          <circle cx="{cx-s*0.09:.2f}" cy="{cy+s*0.07:.2f}" r="{s*0.09:.2f}" fill="{palette['fg']}" opacity="0.18"/>
        </g>
        '''

    text_layers: list[str] = []
    for pos, txt in intents:
        safe = html.escape(txt)
        if pos == "top_left":
            text_layers.append(
                f'<text x="{width*0.06:.2f}" y="{height*0.10:.2f}" font-family="PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{max(20, int(width*0.042))}" font-weight="800" fill="{palette["fg"]}">{safe}</text>'
            )
        elif pos == "bottom":
            text_layers.append(
                f'<text x="{width*0.50:.2f}" y="{height*0.93:.2f}" text-anchor="middle" font-family="PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{max(28, int(width*0.062))}" font-weight="900" fill="{palette["fg"]}" stroke="#000" stroke-opacity="0.25" stroke-width="2">{safe}</text>'
            )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{palette['bg_a']}"/>
      <stop offset="100%" stop-color="{palette['bg_b']}"/>
    </linearGradient>
    <radialGradient id="soft" gradientUnits="userSpaceOnUse" cx="{width*0.50:.2f}" cy="{height*0.35:.2f}" r="{max(width, height)*0.55:.2f}">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.32"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="100%" height="100%" fill="url(#bg)"/>
  <rect width="100%" height="100%" fill="url(#soft)"/>
  <g>{' '.join(deco)}</g>
  <g>{particles}</g>
  {body}
  <g>{' '.join(text_layers)}</g>
</svg>'''


def _compose_svg(prompt: str, width: int, height: int) -> str:
    if _is_cover_prompt(prompt):
        return _compose_cover_svg(prompt, width, height)
    return _compose_illustration_svg(prompt, width, height)


def export_svg_to_png(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)

    def run(cmd: list[str]) -> bool:
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return png_path.exists() and png_path.stat().st_size > 0
        except Exception:
            return False

    if shutil.which("rsvg-convert"):
        if run(["rsvg-convert", "-w", str(width), "-h", str(height), str(svg_path), "-o", str(png_path)]):
            return
    if shutil.which("inkscape"):
        if run(["inkscape", str(svg_path), f"--export-filename={png_path}", f"--export-width={width}", f"--export-height={height}"]):
            return
    if shutil.which("qlmanage"):
        tmpdir = Path(subprocess.check_output(["mktemp", "-d"], text=True).strip())
        preview_name = f"{svg_path.name}.png"
        preview_path = tmpdir / preview_name
        try:
            try:
                subprocess.run(
                    ["qlmanage", "-t", "-s", str(max(width, height)), "-o", str(tmpdir), str(svg_path)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                ql_ok = True
            except Exception:
                ql_ok = False
            if ql_ok:
                if preview_path.exists():
                    shutil.copyfile(preview_path, png_path)
                    if png_path.exists() and png_path.stat().st_size > 0:
                        return
        finally:
            try:
                for p in tmpdir.iterdir():
                    p.unlink(missing_ok=True)
                tmpdir.rmdir()
            except Exception:
                pass

    if shutil.which("sips"):
        if run(["sips", "-s", "format", "png", str(svg_path), "--out", str(png_path)]):
            if width > 0 and height > 0:
                run(["sips", "-z", str(height), str(width), str(png_path)])
            if png_path.exists() and png_path.stat().st_size > 0:
                return
    if shutil.which("magick"):
        if run(["magick", "-background", "none", str(svg_path), str(png_path)]):
            return

    if EXPORT_FALLBACK_SCRIPT.exists() and run(["bash", str(EXPORT_FALLBACK_SCRIPT), str(svg_path), str(png_path), str(width), str(height)]):
        return

    raise RuntimeError("No local SVG renderer found. Install rsvg-convert, inkscape, ImageMagick, or ensure macOS sips supports SVG.")


def generate_image(prompt: str, output: str | Path, width: int, height: int, svg_output: str | Path | None = None) -> dict[str, Any]:
    png_path = Path(output).expanduser().resolve()
    svg_path = Path(svg_output).expanduser().resolve() if svg_output else png_path.with_suffix(".svg")

    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_content = _compose_svg(prompt, width, height)
    svg_path.write_text(svg_content, encoding="utf-8")
    export_svg_to_png(svg_path, png_path, width, height)

    return {
        "mode": "local-svg-to-png",
        "prompt": prompt,
        "svg": str(svg_path),
        "png": str(png_path),
        "width": width,
        "height": height,
        "composition": "cover" if _is_cover_prompt(prompt) else "illustration",
    }


def _load_manifest(project_dir: Path) -> tuple[Path | None, dict[str, Any]]:
    manifest_path = project_dir / "manifest.json"
    if not manifest_path.exists():
        return None, {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return manifest_path, data
    except json.JSONDecodeError:
        pass
    return manifest_path, {}


def _save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_openclaw_assets(project_dir: str | Path, prompt: str) -> dict[str, Any]:
    project = Path(project_dir).expanduser().resolve()
    if not project.exists():
        raise FileNotFoundError(f"Project directory not found: {project}")

    assets = project / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    thumbnail_png = assets / "thumbnail.png"
    thumbnail_svg = assets / "thumbnail.svg"
    icon_png = assets / "icon.png"
    icon_svg = assets / "icon.svg"

    generate_image(
        prompt=f"{prompt} cover thumbnail 海报",
        output=thumbnail_png,
        width=1024,
        height=576,
        svg_output=thumbnail_svg,
    )
    generate_image(
        prompt=f"{prompt} icon illustration",
        output=icon_png,
        width=384,
        height=384,
        svg_output=icon_svg,
    )

    manifest_path, manifest = _load_manifest(project)
    manifest_updated = False
    if manifest_path and isinstance(manifest, dict):
        if manifest.get("thumbnail") != "assets/thumbnail.png":
            manifest["thumbnail"] = "assets/thumbnail.png"
            manifest_updated = True
        if manifest.get("icon") != "assets/icon.png":
            manifest["icon"] = "assets/icon.png"
            manifest_updated = True
        if manifest_updated:
            _save_manifest(manifest_path, manifest)

    return {
        "mode": "openclaw-assets-local",
        "project": str(project),
        "thumbnail_png": str(thumbnail_png),
        "thumbnail_svg": str(thumbnail_svg),
        "icon_png": str(icon_png),
        "icon_svg": str(icon_svg),
        "manifest": str(manifest_path) if manifest_path else None,
        "manifest_updated": manifest_updated,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local free text-to-image by SVG then PNG")
    parser.add_argument("--prompt", required=True, help="Text prompt")
    parser.add_argument("--output", help="Output PNG path")
    parser.add_argument("--svg-output", help="Output SVG path (optional)")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--openclaw-project", help="Generate assets/thumbnail+icon for OpenClaw project")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        if args.openclaw_project:
            result = generate_openclaw_assets(args.openclaw_project, args.prompt)
        else:
            output = args.output
            if not output:
                stem = _slugify(args.prompt)[:48]
                output = str(Path.cwd() / f"{stem}.png")
            result = generate_image(args.prompt, output, args.width, args.height, args.svg_output)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import math
import mimetypes
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


EXPORT_FALLBACK_SCRIPT = Path("/Users/chunima/.codex/skills/svg-png-cover-generator/scripts/export_svg_to_png.sh")
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT.parent / "output"
STORY_PLAN_SCHEMA_PATH = REPO_ROOT / "references" / "story-plan.schema.json"
STORY_PLAN_TEMPLATE_PATH = REPO_ROOT / "references" / "story-plan.template.json"
SUPPORTED_PAGE_KINDS = {
    "article_page",
    "text_cover",
    "mechanism",
    "checklist",
    "qa",
    "catalog",
    "map",
    "comparison",
    "flow",
    "timeline",
    "article_note",
    "custom_svg",
}
SUPPORTED_THEMES = {"auto", "light", "dark"}
SUPPORTED_DENSITIES = {"auto", "comfy", "compact"}
SUPPORTED_SERIES_STYLES = {"auto", "loose", "unified"}
SUPPORTED_SECTION_ROLES = {"auto", "cover", "chapter", "body", "summary"}
SUPPORTED_SURFACE_STYLES = {"auto", "soft", "card", "minimal", "editorial"}
SUPPORTED_ACCENTS = {"auto", "blue", "green", "warm", "rose"}
SUPPORTED_TONES = {"auto", "calm", "playful", "bold", "editorial"}
SUPPORTED_DECOR_LEVELS = {"auto", "none", "low", "medium"}
SUPPORTED_EMOJI_POLICIES = {"auto", "none", "sparse", "expressive"}
SUPPORTED_EMOJI_RENDER_MODES = {"auto", "font", "svg", "mono", "none"}
SUPPORTED_COVER_LAYOUTS = {"auto", "title_first", "hero_emoji_top"}
CURRENT_EMOJI_RENDER_MODE = "font"


def _resolved_emoji_render_mode(value: str = "auto") -> str:
    if value in {"font", "svg", "mono", "none"}:
        return value
    return "svg" if sys.platform.startswith("linux") else "font"


def _set_current_emoji_render_mode(value: str = "auto") -> str:
    global CURRENT_EMOJI_RENDER_MODE
    CURRENT_EMOJI_RENDER_MODE = _resolved_emoji_render_mode(value)
    return CURRENT_EMOJI_RENDER_MODE


def _normalize_emoji_token(value: str) -> str:
    return value.replace("\ufe0f", "").replace("\u200d", "").strip()


def _emoji_svg_markup(emoji: str, x: float, baseline_y: float, size: int, anchor: str = "start") -> str:
    token = _normalize_emoji_token(emoji)
    if not token:
        return ""
    width = float(size)
    left = x - width / 2 if anchor == "middle" else x
    top = baseline_y - size * 0.84
    cx = left + width * 0.5
    cy = top + size * 0.5
    stroke = max(2.0, size * 0.035)

    def wrap(inner: str) -> str:
        return f'<g transform="translate({left:.2f},{top:.2f})">{inner}</g>'

    if token in {"✅", "☑"}:
        return wrap(
            f'<rect x="{width*0.12:.2f}" y="{size*0.12:.2f}" width="{width*0.76:.2f}" height="{size*0.76:.2f}" rx="{size*0.18:.2f}" fill="#43C56B"/>'
            f'<path d="M {width*0.28:.2f} {size*0.52:.2f} L {width*0.43:.2f} {size*0.67:.2f} L {width*0.73:.2f} {size*0.34:.2f}" '
            f'stroke="#FFFFFF" stroke-width="{stroke*2.0:.2f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    if token in {"❓", "❔"}:
        return wrap(
            f'<circle cx="{width*0.50:.2f}" cy="{size*0.44:.2f}" r="{size*0.30:.2f}" fill="#7C63D8"/>'
            f'<text x="{width*0.50:.2f}" y="{size*0.58:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="{size*0.50:.2f}" font-weight="900" fill="#FFFFFF">?</text>'
        )
    if token == "⚠":
        return wrap(
            f'<path d="M {width*0.50:.2f} {size*0.12:.2f} L {width*0.88:.2f} {size*0.84:.2f} L {width*0.12:.2f} {size*0.84:.2f} Z" fill="#FFC83D"/>'
            f'<rect x="{width*0.46:.2f}" y="{size*0.32:.2f}" width="{width*0.08:.2f}" height="{size*0.24:.2f}" rx="{size*0.02:.2f}" fill="#5A4300"/>'
            f'<circle cx="{width*0.50:.2f}" cy="{size*0.68:.2f}" r="{size*0.04:.2f}" fill="#5A4300"/>'
        )
    if token == "💡":
        return wrap(
            f'<circle cx="{width*0.50:.2f}" cy="{size*0.38:.2f}" r="{size*0.24:.2f}" fill="#FFD95A"/>'
            f'<rect x="{width*0.38:.2f}" y="{size*0.56:.2f}" width="{width*0.24:.2f}" height="{size*0.12:.2f}" rx="{size*0.04:.2f}" fill="#FDBA2D"/>'
            f'<rect x="{width*0.40:.2f}" y="{size*0.68:.2f}" width="{width*0.20:.2f}" height="{size*0.09:.2f}" rx="{size*0.03:.2f}" fill="#6B5A2B"/>'
            f'<path d="M {width*0.50:.2f} {size*0.04:.2f} L {width*0.50:.2f} {size*0.14:.2f} M {width*0.20:.2f} {size*0.18:.2f} L {width*0.28:.2f} {size*0.24:.2f} M {width*0.80:.2f} {size*0.18:.2f} L {width*0.72:.2f} {size*0.24:.2f}" stroke="#FFCC33" stroke-width="{stroke:.2f}" stroke-linecap="round"/>'
        )
    if token == "🚀":
        return wrap(
            f'<path d="M {width*0.56:.2f} {size*0.12:.2f} C {width*0.74:.2f} {size*0.22:.2f} {width*0.78:.2f} {size*0.44:.2f} {width*0.62:.2f} {size*0.62:.2f} L {width*0.42:.2f} {size*0.82:.2f} L {width*0.32:.2f} {size*0.72:.2f} L {width*0.52:.2f} {size*0.52:.2f} C {width*0.70:.2f} {size*0.36:.2f} {width*0.66:.2f} {size*0.18:.2f} {width*0.56:.2f} {size*0.12:.2f} Z" fill="#E9EEF9"/>'
            f'<circle cx="{width*0.57:.2f}" cy="{size*0.36:.2f}" r="{size*0.08:.2f}" fill="#5BA9FF"/>'
            f'<path d="M {width*0.36:.2f} {size*0.70:.2f} L {width*0.22:.2f} {size*0.78:.2f} L {width*0.32:.2f} {size*0.60:.2f} Z" fill="#F05C7C"/>'
            f'<path d="M {width*0.52:.2f} {size*0.86:.2f} L {width*0.46:.2f} {size*1.00:.2f} L {width*0.62:.2f} {size*0.90:.2f} Z" fill="#FFB347"/>'
        )
    if token == "🤖":
        return wrap(
            f'<rect x="{width*0.20:.2f}" y="{size*0.22:.2f}" width="{width*0.60:.2f}" height="{size*0.48:.2f}" rx="{size*0.12:.2f}" fill="#8EC5FF"/>'
            f'<rect x="{width*0.30:.2f}" y="{size*0.12:.2f}" width="{width*0.40:.2f}" height="{size*0.14:.2f}" rx="{size*0.06:.2f}" fill="#5E8EE8"/>'
            f'<path d="M {width*0.50:.2f} {size*0.04:.2f} L {width*0.50:.2f} {size*0.14:.2f}" stroke="#5E8EE8" stroke-width="{stroke:.2f}" stroke-linecap="round"/>'
            f'<circle cx="{width*0.38:.2f}" cy="{size*0.45:.2f}" r="{size*0.05:.2f}" fill="#1D2C5B"/>'
            f'<circle cx="{width*0.62:.2f}" cy="{size*0.45:.2f}" r="{size*0.05:.2f}" fill="#1D2C5B"/>'
            f'<rect x="{width*0.37:.2f}" y="{size*0.56:.2f}" width="{width*0.26:.2f}" height="{size*0.06:.2f}" rx="{size*0.03:.2f}" fill="#1D2C5B"/>'
        )
    if token == "💥":
        pts = [
            (0.50, 0.02), (0.60, 0.26), (0.92, 0.12), (0.74, 0.40), (0.98, 0.52),
            (0.72, 0.62), (0.88, 0.94), (0.56, 0.78), (0.40, 1.00), (0.32, 0.72),
            (0.06, 0.86), (0.18, 0.58), (0.00, 0.44), (0.26, 0.34), (0.12, 0.10), (0.40, 0.22)
        ]
        poly = " ".join(f"{width*px:.2f},{size*py:.2f}" for px, py in pts)
        return wrap(
            f'<polygon points="{poly}" fill="#FF9B42"/>'
            f'<polygon points="{" ".join(f"{width*(0.50 + (px-0.50)*0.58):.2f},{size*(0.52 + (py-0.52)*0.58):.2f}" for px, py in pts)}" fill="#FFD85A"/>'
        )
    if token == "📌":
        return wrap(
            f'<circle cx="{width*0.50:.2f}" cy="{size*0.24:.2f}" r="{size*0.16:.2f}" fill="#FF6A86"/>'
            f'<path d="M {width*0.50:.2f} {size*0.38:.2f} L {width*0.68:.2f} {size*0.62:.2f} L {width*0.60:.2f} {size*0.68:.2f} L {width*0.44:.2f} {size*0.48:.2f} Z" fill="#D64A68"/>'
            f'<path d="M {width*0.44:.2f} {size*0.48:.2f} L {width*0.28:.2f} {size*0.92:.2f}" stroke="#5A4A4A" stroke-width="{stroke:.2f}" stroke-linecap="round"/>'
        )
    if token == "📋":
        return wrap(
            f'<rect x="{width*0.24:.2f}" y="{size*0.16:.2f}" width="{width*0.52:.2f}" height="{size*0.68:.2f}" rx="{size*0.08:.2f}" fill="#F3F6FF"/>'
            f'<rect x="{width*0.36:.2f}" y="{size*0.10:.2f}" width="{width*0.28:.2f}" height="{size*0.12:.2f}" rx="{size*0.05:.2f}" fill="#7C63D8"/>'
            f'<path d="M {width*0.34:.2f} {size*0.36:.2f} L {width*0.64:.2f} {size*0.36:.2f} M {width*0.34:.2f} {size*0.52:.2f} L {width*0.64:.2f} {size*0.52:.2f} M {width*0.34:.2f} {size*0.68:.2f} L {width*0.58:.2f} {size*0.68:.2f}" stroke="#8C96AE" stroke-width="{stroke:.2f}" stroke-linecap="round"/>'
        )
    if token == "⚖":
        return wrap(
            f'<path d="M {width*0.50:.2f} {size*0.18:.2f} L {width*0.50:.2f} {size*0.70:.2f} M {width*0.30:.2f} {size*0.30:.2f} L {width*0.70:.2f} {size*0.30:.2f} M {width*0.50:.2f} {size*0.18:.2f} L {width*0.42:.2f} {size*0.10:.2f} M {width*0.50:.2f} {size*0.18:.2f} L {width*0.58:.2f} {size*0.10:.2f}" stroke="#6E5A2C" stroke-width="{stroke:.2f}" stroke-linecap="round"/>'
            f'<path d="M {width*0.30:.2f} {size*0.30:.2f} L {width*0.22:.2f} {size*0.46:.2f} M {width*0.30:.2f} {size*0.30:.2f} L {width*0.38:.2f} {size*0.46:.2f}" stroke="#6E5A2C" stroke-width="{stroke:.2f}" stroke-linecap="round"/>'
            f'<path d="M {width*0.70:.2f} {size*0.30:.2f} L {width*0.62:.2f} {size*0.46:.2f} M {width*0.70:.2f} {size*0.30:.2f} L {width*0.78:.2f} {size*0.46:.2f}" stroke="#6E5A2C" stroke-width="{stroke:.2f}" stroke-linecap="round"/>'
            f'<path d="M {width*0.18:.2f} {size*0.48:.2f} Q {width*0.30:.2f} {size*0.62:.2f} {width*0.42:.2f} {size*0.48:.2f} Z" fill="#7AA2FF"/>'
            f'<path d="M {width*0.58:.2f} {size*0.48:.2f} Q {width*0.70:.2f} {size*0.62:.2f} {width*0.82:.2f} {size*0.48:.2f} Z" fill="#F28CC8"/>'
            f'<rect x="{width*0.38:.2f}" y="{size*0.72:.2f}" width="{width*0.24:.2f}" height="{size*0.07:.2f}" rx="{size*0.03:.2f}" fill="#6E5A2C"/>'
        )
    if token == "🔄":
        return wrap(
            f'<path d="M {width*0.22:.2f} {size*0.52:.2f} C {width*0.24:.2f} {size*0.26:.2f} {width*0.64:.2f} {size*0.20:.2f} {width*0.76:.2f} {size*0.38:.2f}" stroke="#4F7FF7" stroke-width="{stroke*1.8:.2f}" fill="none" stroke-linecap="round"/>'
            f'<path d="M {width*0.68:.2f} {size*0.26:.2f} L {width*0.82:.2f} {size*0.30:.2f} L {width*0.74:.2f} {size*0.42:.2f}" fill="#4F7FF7"/>'
            f'<path d="M {width*0.78:.2f} {size*0.50:.2f} C {width*0.76:.2f} {size*0.78:.2f} {width*0.36:.2f} {size*0.82:.2f} {width*0.24:.2f} {size*0.64:.2f}" stroke="#43C56B" stroke-width="{stroke*1.8:.2f}" fill="none" stroke-linecap="round"/>'
            f'<path d="M {width*0.32:.2f} {size*0.76:.2f} L {width*0.18:.2f} {size*0.72:.2f} L {width*0.26:.2f} {size*0.60:.2f}" fill="#43C56B"/>'
        )
    if token == "🗺":
        return wrap(
            f'<path d="M {width*0.14:.2f} {size*0.20:.2f} L {width*0.36:.2f} {size*0.14:.2f} L {width*0.56:.2f} {size*0.22:.2f} L {width*0.78:.2f} {size*0.16:.2f} L {width*0.86:.2f} {size*0.78:.2f} L {width*0.64:.2f} {size*0.84:.2f} L {width*0.44:.2f} {size*0.76:.2f} L {width*0.22:.2f} {size*0.82:.2f} Z" fill="#D9F0D4"/>'
            f'<path d="M {width*0.36:.2f} {size*0.14:.2f} L {width*0.44:.2f} {size*0.76:.2f} M {width*0.56:.2f} {size*0.22:.2f} L {width*0.64:.2f} {size*0.84:.2f}" stroke="#89B97A" stroke-width="{stroke:.2f}"/>'
            f'<path d="M {width*0.56:.2f} {size*0.46:.2f} C {width*0.56:.2f} {size*0.34:.2f} {width*0.68:.2f} {size*0.30:.2f} {width*0.68:.2f} {size*0.44:.2f} C {width*0.68:.2f} {size*0.54:.2f} {width*0.56:.2f} {size*0.64:.2f} {width*0.56:.2f} {size*0.72:.2f} C {width*0.56:.2f} {size*0.64:.2f} {width*0.44:.2f} {size*0.54:.2f} {width*0.44:.2f} {size*0.44:.2f} C {width*0.44:.2f} {size*0.30:.2f} {width*0.56:.2f} {size*0.34:.2f} {width*0.56:.2f} {size*0.46:.2f} Z" fill="#FF6A86"/>'
        )
    if token == "🧩":
        return wrap(
            f'<path d="M {width*0.26:.2f} {size*0.24:.2f} H {width*0.46:.2f} C {width*0.44:.2f} {size*0.14:.2f} {width*0.50:.2f} {size*0.08:.2f} {width*0.60:.2f} {size*0.08:.2f} C {width*0.72:.2f} {size*0.08:.2f} {width*0.78:.2f} {size*0.16:.2f} {width*0.76:.2f} {size*0.26:.2f} H {width*0.84:.2f} V {size*0.46:.2f} C {width*0.94:.2f} {size*0.44:.2f} {size*0.94:.2f} {size*0.50:.2f} {size*0.94:.2f} {size*0.60:.2f} C {size*0.94:.2f} {size*0.72:.2f} {width*0.86:.2f} {size*0.78:.2f} {width*0.76:.2f} {size*0.76:.2f} V {size*0.84:.2f} H {width*0.26:.2f} V {size*0.64:.2f} C {width*0.16:.2f} {size*0.66:.2f} {width*0.10:.2f} {size*0.60:.2f} {width*0.10:.2f} {size*0.50:.2f} C {width*0.10:.2f} {size*0.40:.2f} {width*0.16:.2f} {size*0.34:.2f} {width*0.26:.2f} {size*0.36:.2f} Z" fill="#8B6CFF"/>'
        )
    if token == "✨":
        return wrap(
            f'<path d="M {width*0.50:.2f} {size*0.08:.2f} L {width*0.58:.2f} {size*0.42:.2f} L {width*0.92:.2f} {size*0.50:.2f} L {width*0.58:.2f} {size*0.58:.2f} L {width*0.50:.2f} {size*0.92:.2f} L {width*0.42:.2f} {size*0.58:.2f} L {width*0.08:.2f} {size*0.50:.2f} L {width*0.42:.2f} {size*0.42:.2f} Z" fill="#FFD95A"/>'
        )
    if token == "🤔":
        return wrap(
            f'<circle cx="{width*0.50:.2f}" cy="{size*0.40:.2f}" r="{size*0.28:.2f}" fill="#FFD76A"/>'
            f'<circle cx="{width*0.40:.2f}" cy="{size*0.38:.2f}" r="{size*0.04:.2f}" fill="#5A4622"/>'
            f'<circle cx="{width*0.58:.2f}" cy="{size*0.41:.2f}" r="{size*0.04:.2f}" fill="#5A4622"/>'
            f'<path d="M {width*0.35:.2f} {size*0.30:.2f} L {width*0.47:.2f} {size*0.26:.2f}" stroke="#5A4622" stroke-width="{stroke:.2f}" stroke-linecap="round"/>'
            f'<path d="M {width*0.44:.2f} {size*0.52:.2f} Q {width*0.52:.2f} {size*0.48:.2f} {width*0.60:.2f} {size*0.54:.2f}" stroke="#5A4622" stroke-width="{stroke:.2f}" fill="none" stroke-linecap="round"/>'
            f'<path d="M {width*0.62:.2f} {size*0.62:.2f} Q {width*0.70:.2f} {size*0.56:.2f} {width*0.76:.2f} {size*0.70:.2f}" stroke="#F0C08A" stroke-width="{stroke*2.0:.2f}" fill="none" stroke-linecap="round"/>'
        )
    return ""


def _slugify(text: str) -> str:
    text = _clean_line(text)
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1F]+', "", text)
    normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", safe).strip("-").lower()
    if normalized:
        return normalized
    compact = safe[:12]
    compact = re.sub(r"\s+", "", compact)
    return compact or "image"


def _stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def _timestamp_slug(prefix: str, text: str, suffix: str = "") -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = _slugify(text)[:36]
    core = f"{stamp}-{prefix}-{slug}" if slug else f"{stamp}-{prefix}"
    return f"{core}-{suffix}" if suffix else core


def _default_output_label(prompt: str | None, story_plan: dict[str, Any] | None = None) -> str:
    if story_plan:
        for key in ["title", "subtitle"]:
            value = story_plan.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if not prompt:
        return "image"
    for labels in (["标题", "主标题", "title"], ["heading", "章节"], ["副标题", "subtitle"]):
        value = _extract_labeled_value(prompt, labels)
        if value:
            return value
    return prompt


def _is_cover_prompt(prompt: str) -> bool:
    lower = prompt.lower()
    keys = ["cover", "thumbnail", "poster", "banner", "海报", "封面", "宣传图", "主视觉"]
    return any(k in lower for k in keys)


def _is_infographic_prompt(prompt: str) -> bool:
    lower = prompt.lower()
    keys = ["infographic", "信息图", "知识卡片", "图解", "路线图", "对比图", "timeline", "架构图", "流程图"]
    return any(k in lower for k in keys) or _looks_like_article_prompt(prompt)


def _is_text_cover_prompt(prompt: str) -> bool:
    lower = prompt.lower()
    keys = ["text cover", "文字封面", "title card", "文字海报", "标题页", "封面标题"]
    return any(k in lower for k in keys)


def _clean_line(text: str) -> str:
    text = re.sub(r"^[#>\-\*\s]+", "", text.strip())
    text = re.sub(r"^[\u2600-\u27BF\U0001F300-\U0001FAFF]+\s*", "", text)
    text = re.sub(r"^\d+\.\s*", "", text)
    return text.strip(" -—•\t")


def _strip_image_directives(text: str) -> str:
    return re.sub(r"(?:^|\s)(?:插图文件|IMAGE_FILE)\s*[:：]\s*[^\n]+", "", text, flags=re.IGNORECASE).strip()


def _extract_story_image_paths(text: str) -> list[str]:
    paths: list[str] = []
    for m in re.finditer(r"(?:^|\s)(?:插图文件|IMAGE_FILE)\s*[:：]\s*([^\n]+)", text, flags=re.IGNORECASE):
        value = m.group(1).strip().strip('"')
        if value:
            paths.append(value)
    return paths


def _normalize_dedupe_text(text: str) -> str:
    return re.sub(r'[\"“”\s，。！？!：:；;\-—·]+', "", text)


def _is_section_heading(line: str) -> bool:
    if not line:
        return False
    if len(line) <= 28 and any(token in line for token in ["为什么", "写在最后", "联系我们", "官方公告", "震撼数据", "硬伤", "更配", "配置", "步骤"]):
        return True
    if len(line) <= 32 and re.search(r"[？!?！]$", line):
        return True
    if (
        len(line) <= 26
        and not re.search(r"[。；;，,]", line)
        and any(token in line for token in ["第", "场景", "能力", "使用", "龙虾", "智能体", "部署", "召唤", "详解", "指南", "选项", "课"])
    ):
        return True
    if len(line) <= 22 and re.match(r"^[^：:，,。；;]{1,10}[：:][^，,。；;]{0,12}$", line):
        return True
    if re.match(r'^[0-9一二三四五六七八九十]+[、\.]', line):
        return True
    if re.match(r'^[\u2460-\u2473\u2776-\u277F\U0001F51F\U0001F522]', line):
        return True
    if any(ord(ch) > 0xFFFF for ch in line[:2]) and len(line) <= 32:
        return True
    return False


def _meaningful_lines(prompt: str) -> list[str]:
    lines: list[str] = []
    for raw in prompt.splitlines():
        line = _clean_line(raw)
        if not line or set(line) <= {"-", "_", "—", " "}:
            continue
        lines.append(line)
    return lines


def _looks_like_article_prompt(prompt: str) -> bool:
    lines = _meaningful_lines(prompt)
    bullet_count = len(re.findall(r"(?:^|\n)\s*(?:[-*•]|\d+\.)\s*", prompt))
    paragraphish = len(re.findall(r"[。！？!?]", prompt))
    if len(prompt) >= 220 and (len(lines) >= 6 or bullet_count >= 3):
        return True
    if len(prompt) >= 320 and paragraphish >= 4:
        return True
    return False


def _pick_stat_phrase(prompt: str) -> str | None:
    matches = re.findall(r"\d+(?:\.\d+)?\s*(?:万亿|亿|万|多倍|倍|%)", prompt)
    if not matches:
        return None
    def score(token: str) -> tuple[int, int]:
        unit_weight = 0
        compact = token.replace(" ", "")
        for idx, unit in enumerate(["万亿", "亿", "万", "多倍", "倍", "%"]):
            if unit in token:
                unit_weight = 20 - idx
                break
        digits = int(re.sub(r"\D", "", compact) or "0")
        return (unit_weight, digits)
    return max(matches, key=score)


def _article_line_score(text: str) -> int:
    score = 0
    if len(text) < 8 or len(text) > 52:
        return -99
    if any(token in text for token in ["家人们", "炸了", "out"]):
        score -= 8
    if any(token in text for token in ["值得升", "结论", "意味着", "一句话概括", "最重要", "最值得关注"]):
        score += 8
    if any(token in text for token in ["建议", "一定", "先", "再", "不要", "记住一句话", "提醒", "避坑"]):
        score += 7
    if any(token in text for token in ["风险", "卡死", "失败", "异常", "告警", "拦下来", "配置非法"]):
        score += 7
    if any(token in text for token in ["正式定名", "优先推荐", "官方", "发布试用", "明确使用", "中文名"]):
        score += 7
    if any(token in text for token in ["调用量", "增长", "关键指标", "突破", "万亿", "倍", "%"]):
        score += 6
    if any(token in text for token in ["既体现", "强调", "扩展", "原因", "本质", "语义", "多模态", "遵循"]):
        score += 5
    if any(token in text for token in ["词元", "Token", "Prompt", "OpenClaw", "MCP", "Feishu", "Lark"]):
        score += 3
    if "2026 年 3 月" in text or "3 月 25 日" in text:
        score += 1
    return score


def _derive_article_copy(prompt: str, mode: str = "infographic") -> dict[str, Any]:
    prompt = _strip_image_directives(prompt)
    lines = _meaningful_lines(prompt)
    title = lines[0] if lines else "文章重点提炼"
    subtitle = ""
    subtitle_keywords = ["正式定名", "优先推荐", "官方", "词元", "Token"]
    for line in lines[1:]:
        if len(line) < 8 or len(line) > 30:
            continue
        if any(token in line for token in ["家人们", "炸了", "out"]):
            continue
        if any(token in line for token in subtitle_keywords):
            subtitle = line
            break
    if not subtitle:
        for line in lines[1:]:
            if len(line) >= 10 and not any(token in line for token in ["家人们", "炸了", "out"]):
                subtitle = line
                break
    if not subtitle:
        subtitle = "一图看懂核心结论、关键数据和原因解释"

    candidate_lines: list[str] = []
    explicit_bullets = re.findall(r"(?:^|\n)\s*(?:[-*•]|\d+\.)\s*(.+)", prompt, flags=re.MULTILINE)
    candidate_lines.extend(explicit_bullets)
    candidate_lines.extend(lines[1:])
    candidate_lines.extend(re.split(r"[。！？!\n]", prompt))

    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for raw in candidate_lines:
        clean = re.sub(r"\s+", " ", _clean_line(raw)).strip(" ,，。；;")
        dedupe_key = _normalize_dedupe_text(clean)
        if not clean or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        ranked.append((_article_line_score(clean), clean))

    ranked.sort(key=lambda item: item[0], reverse=True)
    official = [text for score, text in ranked if score > 0 and any(token in text for token in ["正式定名", "优先推荐", "官方", "明确使用", "中文名"])]
    stats = [text for score, text in ranked if score > 0 and any(token in text for token in ["调用量", "增长", "关键指标", "突破", "万亿", "倍", "%"])]
    reasons = [text for score, text in ranked if score > 0 and any(token in text for token in ["既体现", "强调", "扩展", "原因", "本质", "语义", "多模态", "遵循"])]
    bullets = []
    for group in [official, stats, reasons]:
        for text in group:
            if text not in bullets:
                bullets.append(text)
                break
    for score, text in ranked:
        if score <= 0:
            continue
        if text not in bullets:
            bullets.append(text)
        if len(bullets) >= 6:
            break

    if not bullets:
        bullets = [
            "提炼文章主结论，避免整段文字直接堆到画面上",
            "抓取最关键的数据、结论和解释",
            "优先生成适合手机阅读的知识图结构",
        ]

    kicker = "文章图解" if mode == "infographic" else "ARTICLE"
    emphasis = _pick_stat_phrase(prompt) or ""
    footer = _extract_labeled_value(prompt, ["页脚", "底部文案", "footer"]) or ""
    return {
        "title": title,
        "subtitle": subtitle,
        "kicker": kicker,
        "emphasis": emphasis,
        "footer": footer,
        "bullets": bullets[:6],
    }


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


def _extract_named_value(prompt: str, labels: list[str]) -> str | None:
    for label in labels:
        match = re.search(rf"{label}\s*(?:[:：]|是|写)?\s*([^\n]+)", prompt, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip().strip('"“”')
            if value:
                return value
    return None


def _extract_labeled_value(prompt: str, labels: list[str]) -> str | None:
    all_labels = [
        "主标题",
        "副标题",
        "标题",
        "subtitle",
        "title",
        "角标",
        "badge",
        "标签",
        "核心数字",
        "重点数字",
        "highlight",
        "要点",
        "bullets",
    ]
    all_labels = sorted(all_labels, key=len, reverse=True)
    labels_lower = {label.lower() for label in labels}
    label_pattern = re.compile(
        rf"(?P<label>{'|'.join(re.escape(label) for label in all_labels)})\s*(?:[:：]|是|写)?\s*",
        flags=re.IGNORECASE,
    )
    matches = list(label_pattern.finditer(prompt))
    for idx, match in enumerate(matches):
        if match.group("label").lower() not in labels_lower:
            continue
        start = match.end()
        end = len(prompt)
        if idx + 1 < len(matches):
            end = min(end, matches[idx + 1].start())
        bullet_match = re.search(r"(?:^|[\s，,；;\n])\d+\.", prompt[start:])
        if bullet_match:
            end = min(end, start + bullet_match.start())
        value = prompt[start:end].strip(" ,，；;。").strip().strip('"“”')
        if value:
            return value
    return None


def _strip_control_directives(text: str) -> str:
    patterns = [
        r"(?:^|\s)(?:主题|theme)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:页面密度|密度|density)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:系列风格|统一程度|series-style|series_style)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:页面角色|章节角色|section-role|section_role)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:页面风格|风格|surface-style|style)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:强调色|accent)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:语气|气质|tone)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:装饰密度|装饰程度|decor-level|decor_level)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:表情策略|emoji-policy|emoji_policy)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:表情渲染|emoji-render-mode|emoji_render_mode)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:封面布局|cover-layout|cover_layout)\s*[:：]\s*[A-Za-z0-9_\u4e00-\u9fff\-]+",
        r"(?:^|\s)(?:主视觉表情|封面表情|hero-emoji|hero_emoji)\s*[:：]\s*[^\n]+",
    ]
    out = text
    for pattern in patterns:
        out = re.sub(pattern, "", out, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", out).strip()


def _resolve_render_controls(prompt: str) -> dict[str, str]:
    prompt_lower = prompt.lower()
    def direct_value(labels: list[str]) -> str:
        for label in labels:
            m = re.search(
                rf"(?:^|[\s，,；;\n]){re.escape(label)}\s*[:：]\s*([A-Za-z0-9_\u4e00-\u9fff\-]+)",
                prompt,
                flags=re.IGNORECASE,
            )
            if m:
                return m.group(1).strip().lower()
        return ""

    theme_raw = direct_value(["主题", "theme"])
    density_raw = direct_value(["页面密度", "密度", "density"])
    series_style_raw = direct_value(["系列风格", "统一程度", "series-style", "series_style"])
    section_role_raw = direct_value(["页面角色", "章节角色", "section-role", "section_role"])
    style_raw = direct_value(["页面风格", "风格", "surface-style", "style"])
    accent_raw = direct_value(["强调色", "accent"])
    tone_raw = direct_value(["语气", "气质", "tone"])
    decor_raw = direct_value(["装饰密度", "装饰程度", "decor-level", "decor_level"])
    emoji_raw = direct_value(["表情策略", "emoji-policy", "emoji_policy"])
    emoji_render_mode_raw = direct_value(["表情渲染", "emoji-render-mode", "emoji_render_mode"])
    cover_layout_raw = direct_value(["封面布局", "cover-layout", "cover_layout"])
    hero_emoji_raw = _extract_named_value(prompt, ["主视觉表情", "封面表情", "hero-emoji", "hero_emoji"]) or ""

    def normalize_theme(value: str) -> str:
        if value in {"dark", "深色", "夜间", "暗色"}:
            return "dark"
        if value in {"light", "浅色", "明亮", "亮色"}:
            return "light"
        return "auto"

    def normalize_density(value: str) -> str:
        if value in {"compact", "紧凑", "dense"}:
            return "compact"
        if value in {"comfy", "舒展", "宽松", "comfortable"}:
            return "comfy"
        return "auto"

    def normalize_style(value: str) -> str:
        if value in {"card", "卡片", "cards"}:
            return "card"
        if value in {"minimal", "极简"}:
            return "minimal"
        if value in {"editorial", "杂志", "article"}:
            return "editorial"
        if value in {"soft", "柔和"}:
            return "soft"
        return "auto"

    def normalize_series_style(value: str) -> str:
        if value in {"loose", "自由", "松散"}:
            return "loose"
        if value in {"unified", "统一", "系列化", "统一风格"}:
            return "unified"
        return "auto"

    def normalize_section_role(value: str) -> str:
        if value in {"cover", "封面"}:
            return "cover"
        if value in {"chapter", "章节"}:
            return "chapter"
        if value in {"body", "正文"}:
            return "body"
        if value in {"summary", "总结", "结尾"}:
            return "summary"
        return "auto"

    def normalize_accent(value: str) -> str:
        if value in {"blue", "蓝", "蓝色"}:
            return "blue"
        if value in {"green", "绿", "绿色"}:
            return "green"
        if value in {"warm", "orange", "橙", "暖色"}:
            return "warm"
        if value in {"rose", "pink", "粉", "粉色"}:
            return "rose"
        return "auto"

    def normalize_tone(value: str) -> str:
        if value in {"calm", "克制", "冷静", "平静"}:
            return "calm"
        if value in {"playful", "有趣", "活泼", "轻松"}:
            return "playful"
        if value in {"bold", "强势", "大胆"}:
            return "bold"
        if value in {"editorial", "杂志", "编辑感"}:
            return "editorial"
        return "auto"

    def normalize_decor(value: str) -> str:
        if value in {"none", "无", "不要", "关闭"}:
            return "none"
        if value in {"low", "少量", "轻量", "低"}:
            return "low"
        if value in {"medium", "中等", "适中", "中"}:
            return "medium"
        return "auto"

    def normalize_emoji(value: str) -> str:
        if value in {"none", "无", "关闭"}:
            return "none"
        if value in {"sparse", "少量", "稀疏"}:
            return "sparse"
        if value in {"expressive", "丰富", "夸张", "密集"}:
            return "expressive"
        return "auto"

    def normalize_emoji_render_mode(value: str) -> str:
        if value in {"font", "字体", "文本"}:
            return "font"
        if value in {"svg", "矢量", "图形"}:
            return "svg"
        if value in {"mono", "单色", "黑白"}:
            return "mono"
        if value in {"none", "无", "关闭"}:
            return "none"
        return "auto"

    def normalize_cover_layout(value: str) -> str:
        if value in {"title_first", "标题优先", "传统"}:
            return "title_first"
        if value in {"hero_emoji_top", "主视觉表情", "大表情", "表情在上"}:
            return "hero_emoji_top"
        return "auto"

    theme = normalize_theme(theme_raw)
    density = normalize_density(density_raw)
    series_style = normalize_series_style(series_style_raw)
    section_role = normalize_section_role(section_role_raw)
    style = normalize_style(style_raw)
    accent = normalize_accent(accent_raw)
    tone = normalize_tone(tone_raw)
    decor_level = normalize_decor(decor_raw)
    emoji_policy = normalize_emoji(emoji_raw)
    emoji_render_mode = normalize_emoji_render_mode(emoji_render_mode_raw)
    cover_layout = normalize_cover_layout(cover_layout_raw)
    hero_emoji = hero_emoji_raw.strip()

    if theme == "auto" and any(token in prompt_lower for token in ["深色", "夜间", "暗色", "dark mode"]):
        theme = "dark"
    if style == "auto" and any(token in prompt_lower for token in ["极简", "minimal"]):
        style = "minimal"
    if accent == "auto" and any(token in prompt_lower for token in ["绿色", "green"]):
        accent = "green"
    if tone == "auto" and any(token in prompt_lower for token in ["有趣", "活泼", "可爱", "轻松", "玩梗", "趣味"]):
        tone = "playful"
    if decor_level == "auto" and any(token in prompt_lower for token in ["多一点装饰", "更有趣", "活泼些", "丰富一点"]):
        decor_level = "medium"
    if emoji_policy == "auto" and any(token in prompt_lower for token in ["表情", "emoji", "颜文字"]):
        emoji_policy = "sparse"
    if tone == "playful" and decor_level == "auto":
        decor_level = "medium"
    if tone == "playful" and emoji_policy == "auto":
        emoji_policy = "sparse"
    if cover_layout == "auto" and any(token in prompt_lower for token in ["大表情", "主视觉表情", "表情在上"]):
        cover_layout = "hero_emoji_top"

    return {
        "theme": theme,
        "density": density,
        "series_style": series_style,
        "section_role": section_role,
        "style": style,
        "accent": accent,
        "tone": tone,
        "decor_level": decor_level,
        "emoji_policy": emoji_policy,
        "emoji_render_mode": emoji_render_mode,
        "cover_layout": cover_layout,
        "hero_emoji": hero_emoji,
    }


def _parse_bullets(prompt: str) -> list[str]:
    bullets: list[str] = []
    numbered = re.findall(r"\d+\.\s*(.+?)(?=(?:\s+\d+\.|$))", prompt)
    if numbered:
        cleaned = [re.sub(r"\s+", " ", item).strip(" ,，。") for item in numbered]
        return [item for item in cleaned if item][:6]

    for raw in re.split(r"[；;\n]", prompt):
        part = raw.strip()
        if not part:
            continue
        if any(token in part for token in ["1.", "2.", "3.", "4.", "-", "•", "—"]):
            bits = re.split(r"(?:^|\s)(?:\d+\.|-|•|—)\s*", part)
            for bit in bits:
                clean = bit.strip(" ,，。")
                if clean:
                    bullets.append(clean)
    if bullets:
        return bullets[:6]

    # Fallback: split on commas for information-heavy prompts
    if _is_infographic_prompt(prompt):
        parts = [p.strip(" ,，。") for p in re.split(r"[,，]", prompt) if p.strip(" ,，。")]
        filtered = [p for p in parts if len(p) >= 3 and not _is_infographic_prompt(p)]
        return filtered[:6]
    return []


def _wrap_text(text: str, limit: int) -> list[str]:
    if not text:
        return []
    if re.search(r"[\u4e00-\u9fff]", text):
        tokens = re.findall(r"[A-Za-z0-9\-\+\.]+|\s+|[\u4e00-\u9fff]|[^\s]", text)
        lines: list[str] = []
        current = ""
        current_len = 0
        for token in tokens:
            if token.isspace():
                if current and not current.endswith(" "):
                    if current_len + 1 <= limit:
                        current += " "
                        current_len += 1
                continue
            token_len = max(1, len(token))
            if token_len > limit:
                if current:
                    lines.append(current.strip())
                    current = ""
                    current_len = 0
                for i in range(0, len(token), limit):
                    lines.append(token[i:i + limit])
                continue
            if current_len + token_len <= limit:
                current += token
                current_len += token_len
            else:
                if current:
                    lines.append(current.strip())
                current = token
                current_len = token_len
        if current:
            lines.append(current.strip())
        return lines
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if len(word) > limit:
            if current:
                lines.append(current)
                current = ""
            for i in range(0, len(word), limit):
                lines.append(word[i:i + limit])
            continue
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _svg_text_block(
    x: float,
    y: float,
    lines: list[str],
    size: int,
    color: str,
    weight: int = 700,
    anchor: str = "start",
    line_gap: float = 1.2,
) -> str:
    if not lines:
        return ""
    font = "PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, sans-serif"
    emoji_render_mode = CURRENT_EMOJI_RENDER_MODE
    pieces = ["<g>"]
    for idx, line in enumerate(lines):
        line_y = y + idx * size * line_gap
        emoji_only = re.fullmatch(r"[\u2600-\u27BF\U0001F300-\U0001FAFF\ufe0f\u200d]+", line.strip() or "")
        if emoji_only:
            if emoji_render_mode == "none":
                continue
            if emoji_render_mode == "svg":
                svg_emoji = _emoji_svg_markup(line.strip(), x, line_y, int(size), anchor=anchor)
                if svg_emoji:
                    pieces.append(svg_emoji)
                    continue
        leading_emoji = None
        rest = line
        if anchor == "start":
            m = re.match(r"^([\u2600-\u27BF\U0001F300-\U0001FAFF]+)\s*(.*)$", line)
            if m and m.group(2):
                leading_emoji = m.group(1)
                rest = m.group(2)
        if leading_emoji:
            if emoji_render_mode == "none":
                leading_emoji = None
            elif emoji_render_mode == "svg":
                emoji_size = int(size * 1.38)
                emoji_y = line_y
                emoji_x = x
                rest_x = x + emoji_size * 1.05
                svg_emoji = _emoji_svg_markup(leading_emoji, emoji_x, emoji_y, emoji_size, anchor="start")
                if svg_emoji:
                    pieces.append(svg_emoji)
                    pieces.append(
                        f'<text x="{rest_x:.2f}" y="{line_y:.2f}" text-anchor="start" font-family="{font}" '
                        f'font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(rest)}</text>'
                    )
                    continue
            emoji_size = int(size * 1.38)
            emoji_y = line_y
            emoji_x = x
            rest_x = x + emoji_size * 1.05
            pieces.append(
                f'<text x="{emoji_x:.2f}" y="{emoji_y:.2f}" text-anchor="start" font-family="{font}" '
                f'font-size="{emoji_size}" font-weight="{weight}" fill="{color}">{html.escape(leading_emoji)}</text>'
            )
            pieces.append(
                f'<text x="{rest_x:.2f}" y="{line_y:.2f}" text-anchor="start" font-family="{font}" '
                f'font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(rest)}</text>'
            )
        else:
            pieces.append(
                f'<text x="{x:.2f}" y="{line_y:.2f}" text-anchor="{anchor}" font-family="{font}" '
                f'font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(line)}</text>'
            )
    pieces.append("</g>")
    return "".join(pieces)


def _text_block_height(lines: list[str], size: int, line_gap: float = 1.2) -> float:
    if not lines:
        return 0
    return size * (1 + max(0, len(lines) - 1) * line_gap)


def _estimate_line_width(line: str, size: int) -> float:
    units = 0.0
    for ch in line:
        if ch.isspace():
            units += 0.30
        elif re.match(r"[\u4e00-\u9fff]", ch):
            units += 1.00
        elif re.match(r"[A-Z]", ch):
            units += 0.68
        elif re.match(r"[a-z0-9]", ch):
            units += 0.58
        elif re.match(r"[，。！？；：、“”‘’（）【】《》]", ch):
            units += 0.58
        else:
            units += 0.42
    return units * size


def _fit_text_block(
    text: str,
    wrap_limits: list[int],
    size_candidates: list[int],
    max_lines: int,
    max_width_px: float | None = None,
    prefer_single_mixed_short: bool = False,
) -> tuple[list[str], int]:
    if not text:
        return [], size_candidates[-1] if size_candidates else 16
    mixed = bool(re.search(r"[\u4e00-\u9fff]", text) and re.search(r"[A-Za-z]", text))
    compact_text = re.sub(r"\s+", "", text)
    if prefer_single_mixed_short and mixed and len(compact_text) <= 18:
        chosen = size_candidates[0] if size_candidates else 16
        if max_width_px is None or _estimate_line_width(text, chosen) <= max_width_px:
            return [text], chosen
    best_lines: list[str] | None = None
    best_size = size_candidates[-1] if size_candidates else 16
    fallback_score: tuple[int, float] | None = None
    for size in size_candidates:
        if max_width_px is None or _estimate_line_width(text, size) <= max_width_px:
            return [text], size
        for limit in wrap_limits:
            lines = _wrap_text(text, limit)
            width_ok = max_width_px is None or all(_estimate_line_width(line, size) <= max_width_px for line in lines)
            if len(lines) <= max_lines and width_ok:
                return lines, size
            score = (abs(len(lines) - max_lines), max((_estimate_line_width(line, size) for line in lines), default=0))
            if best_lines is None or fallback_score is None or score < fallback_score:
                best_lines = lines
                best_size = size
                fallback_score = score
    return (best_lines or _wrap_text(text, wrap_limits[-1]), best_size)


def _fit_body_block(
    text: str,
    max_width_px: float,
    chinese_wraps: list[int],
    latin_wraps: list[int],
    size_candidates: list[int],
    max_lines: int = 2,
) -> tuple[list[str], int]:
    wraps = chinese_wraps if re.search(r"[\u4e00-\u9fff]", text) else latin_wraps
    return _fit_text_block(
        text,
        wraps,
        size_candidates,
        max_lines,
        max_width_px=max_width_px,
    )


def _article_body_wrap_profile(text: str) -> tuple[list[int], list[int], list[int], float]:
    length = len(re.sub(r"\s+", "", text))
    if re.search(r"https?://|`[^`]+`|[A-Za-z0-9_]+\.[A-Za-z0-9_]+", text):
        return [30, 28, 26], [46, 40, 34], [17, 16, 15], 0.88
    if length <= 28:
        return [30, 28, 26], [42, 38, 34], [25, 23, 21], 1.00
    if length <= 42:
        return [28, 26, 24], [40, 36, 32], [24, 22, 20], 0.98
    if length <= 64:
        return [26, 24, 22], [38, 34, 30], [23, 21, 19], 0.95
    return [24, 22, 20], [36, 32, 28], [22, 20, 18], 0.92


def _article_paragraph_rhythm(text: str, height: int, code_like: bool = False) -> tuple[float, float]:
    if code_like:
        return 1.12, height * 0.022
    length = len(re.sub(r"\s+", "", text))
    if length <= 28:
        return 1.56, height * 0.032
    if length <= 42:
        return 1.50, height * 0.029
    if length <= 64:
        return 1.44, height * 0.025
    return 1.38, height * 0.021


def _image_data_uri(path_text: str) -> str | None:
    path = Path(path_text).expanduser()
    if not path.exists() or not path.is_file():
        return None
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        mime = "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _adaptive_stack_positions(start_y: float, heights: list[float], gaps: list[float]) -> list[float]:
    positions = [start_y]
    current = start_y
    for idx, height in enumerate(heights[:-1]):
        current += height + gaps[idx]
        positions.append(current)
    return positions


def _tight_row_metrics(total_height: int, header_bottom: float, footer_reserved: float, rows: int) -> tuple[float, float]:
    available = max(total_height * 0.32, total_height - header_bottom - footer_reserved)
    gap = max(total_height * 0.014, min(total_height * 0.02, available * 0.04))
    row_h = (available - gap * max(0, rows - 1)) / max(1, rows)
    return row_h, gap


def _normalize_layout_label(text: str) -> str:
    return re.sub(r"[\s\-_/：:（）()【】\[\]·•]+", "", text or "").lower()


def _visible_kicker(copy: dict[str, Any], fallback: str = "") -> str:
    kicker = (copy.get("kicker") or "").strip()
    title = (copy.get("title") or "").strip()
    if not kicker:
        return fallback
    if title and _normalize_layout_label(kicker) == _normalize_layout_label(title):
        return ""
    if title and _normalize_layout_label(kicker) in _normalize_layout_label(title):
        return ""
    return kicker


def _footer_lines(copy: dict[str, Any]) -> list[str]:
    footer = (copy.get("footer") or "").strip()
    return [footer] if footer else []


def _split_trailing_emoji(text: str) -> tuple[str, str]:
    stripped = text.strip()
    match = re.match(r"^(.*?)(?:\s*)([\u2600-\u27BF\U0001F300-\U0001FAFF]+)$", stripped)
    if match and match.group(1).strip():
        return match.group(1).rstrip(), match.group(2)
    return stripped, ""


def _title_emoji_svg(
    base_x: float,
    title_y: float,
    title_lines: list[str],
    title_size: int,
    emoji: str,
    width: int,
    color: str,
    anchor: str = "start",
    scale: float = 1.7,
) -> str:
    if not emoji or not title_lines:
        return ""
    emoji_render_mode = CURRENT_EMOJI_RENDER_MODE
    if emoji_render_mode == "none":
        return ""
    last_line = title_lines[-1]
    line_width = _estimate_line_width(last_line, title_size)
    emoji_size = max(24, int(title_size * scale))
    available_w = max(width * 0.84 - base_x, width * 0.22)
    emoji_w = emoji_size * 1.15
    stack_emoji = (line_width + emoji_w > available_w) or scale >= 2.1
    if anchor == "middle":
        emoji_x = base_x + (line_width * 0.5) + width * 0.06
    else:
        if stack_emoji:
            emoji_x = min(base_x + max(line_width * 0.58, width * 0.24), width * 0.78)
        else:
            emoji_x = min(base_x + line_width + width * 0.035, width * 0.90)
    emoji_y = title_y + (len(title_lines) - 1) * title_size * 1.06 + (emoji_size * (0.86 if stack_emoji else 0.10))
    if emoji_render_mode == "svg":
        svg_emoji = _emoji_svg_markup(emoji, emoji_x, emoji_y, emoji_size, anchor="start")
        if svg_emoji:
            return svg_emoji
    return _svg_text_block(emoji_x, emoji_y, [emoji], emoji_size, color, weight=800, anchor="start")


def _balanced_wrap_lines(
    text: str,
    size: int,
    max_width_px: float,
    max_lines: int = 2,
    prefer_short_tail: bool = False,
) -> list[str] | None:
    stripped = re.sub(r"\s+", " ", text).strip()
    if not stripped:
        return None
    if _estimate_line_width(stripped, size) <= max_width_px:
        return [stripped]
    if max_lines != 2:
        return None
    tokens = re.findall(r"[A-Za-z0-9\-\+\.]+|\s+|[\u4e00-\u9fff]|[^\s]", stripped)
    non_space_positions = [idx for idx, token in enumerate(tokens) if not token.isspace()]
    if len(non_space_positions) < 2:
        return None

    best_lines: list[str] | None = None
    best_score: tuple[float, float, int] | None = None
    total_chars = len(re.sub(r"\s+", "", stripped))
    for cut in non_space_positions[1:]:
        left = "".join(tokens[:cut]).strip()
        right = "".join(tokens[cut:]).strip()
        if not left or not right:
            continue
        left_w = _estimate_line_width(left, size)
        right_w = _estimate_line_width(right, size)
        if left_w > max_width_px or right_w > max_width_px:
            continue
        left_chars = len(re.sub(r"\s+", "", left))
        right_chars = len(re.sub(r"\s+", "", right))
        # Prefer visually balanced lines and avoid orphaned tails.
        balance_penalty = abs(left_w - right_w)
        tail_penalty = 0.0 if min(left_chars, right_chars) >= max(3, total_chars // 4) else 220.0
        split_penalty = abs((left_chars / max(total_chars, 1)) - 0.54) * 100.0
        if prefer_short_tail:
            if 4 <= right_chars <= 5:
                tail_penalty -= 240.0
            elif right_chars == 6:
                tail_penalty -= 80.0
            else:
                tail_penalty += abs(right_chars - 5) * 54.0
            split_penalty += abs((left_chars / max(total_chars, 1)) - 0.70) * 120.0
        score = (tail_penalty + split_penalty + balance_penalty, max(left_w, right_w), abs(left_chars - right_chars))
        if best_score is None or score < best_score:
            best_score = score
            best_lines = [left, right]
    return best_lines


def _split_text_tail_chars(text: str, tail_chars: int) -> tuple[str, str] | None:
    if tail_chars <= 0:
        return None
    stripped = text.strip()
    compact = re.sub(r"\s+", "", stripped)
    if len(compact) <= tail_chars:
        return None
    seen = 0
    idx = len(stripped)
    while idx > 0 and seen < tail_chars:
        idx -= 1
        if not stripped[idx].isspace():
            seen += 1
    left = stripped[:idx].rstrip()
    right = stripped[idx:].strip()
    if not left or not right:
        return None
    return left, right


def _extract_trailing_phrase(text: str) -> tuple[str, str]:
    stripped = re.sub(r"\s+", " ", text).strip()
    match = re.match(r"^(.*?)([A-Za-z0-9][A-Za-z0-9\-\+\.]*(?:\s+[A-Za-z0-9][A-Za-z0-9\-\+\.]*){0,2})$", stripped)
    if not match:
        return stripped, ""
    head = match.group(1).rstrip(" ，,：:")
    tail = match.group(2).strip()
    if not head or not tail:
        return stripped, ""
    if len(tail.split()) > 3:
        return stripped, ""
    return head, tail


def _hero_cover_title_lines(text: str, width: int) -> tuple[list[str], int]:
    explicit_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(explicit_lines) >= 2:
        size_candidates = [max(68, int(width * 0.088)), max(62, int(width * 0.082)), max(56, int(width * 0.076))]
        for candidate_size in size_candidates:
            if all(_estimate_line_width(line, candidate_size) <= width * 0.80 for line in explicit_lines):
                return explicit_lines[:3], candidate_size
        return explicit_lines[:3], size_candidates[-1]
    head, tail = _extract_trailing_phrase(text)
    size_candidates = [max(68, int(width * 0.088)), max(62, int(width * 0.082)), max(56, int(width * 0.076))]
    if tail and re.search(r"[\u4e00-\u9fff]", head):
        for candidate_size in size_candidates:
            if _estimate_line_width(tail, candidate_size) > width * 0.64:
                continue
            head_lines = _balanced_wrap_lines(head, candidate_size, width * 0.80, max_lines=2, prefer_short_tail=False)
            if head_lines and len(head_lines) <= 2:
                lines = head_lines + [tail]
                if len(lines) <= 3:
                    return lines, candidate_size
    return _fit_text_block(
        text,
        [14, 12, 10, 8] if re.search(r"[\u4e00-\u9fff]", text) else [20, 18, 16],
        size_candidates,
        3,
        max_width_px=width * 0.80,
        prefer_single_mixed_short=True,
    )


def _cover_title_lines(text: str, width: int, section_role: str) -> tuple[list[str], int]:
    mixed = bool(re.search(r"[\u4e00-\u9fff]", text) and re.search(r"[A-Za-z]", text))
    if mixed and "：" in text:
        left, right = text.split("：", 1)
        left = (left + "：").strip()
        right = right.strip()
        if left and right:
            left_lines, left_size = _fit_text_block(
                left,
                [22, 20, 18],
                [max(84, int(width * 0.090)), max(76, int(width * 0.082)), max(68, int(width * 0.074))],
                2,
                max_width_px=width * 0.74,
                prefer_single_mixed_short=True,
            )
            right_size_candidates = [max(84, int(width * 0.090)), max(76, int(width * 0.082)), max(68, int(width * 0.074))]
            right_size = right_size_candidates[-1]
            right_lines: list[str] | None = None
            for candidate_size in right_size_candidates:
                tail_split = _split_text_tail_chars(right, 4)
                if tail_split:
                    tail_left, tail_right = tail_split
                    if (
                        _estimate_line_width(tail_left, candidate_size) <= width * 0.78
                        and _estimate_line_width(tail_right, candidate_size) <= width * 0.78
                        and len(re.sub(r"\s+", "", tail_right)) <= 4
                    ):
                        right_lines = [tail_left, tail_right]
                        right_size = candidate_size
                        break
                balanced = _balanced_wrap_lines(
                    right,
                    candidate_size,
                    width * 0.78,
                    max_lines=2,
                    prefer_short_tail=True,
                )
                if balanced and len(balanced) <= 2:
                    right_lines = balanced
                    right_size = candidate_size
                    break
            if not right_lines:
                right_lines, right_size = _fit_text_block(
                    right,
                    [12, 10, 8, 7],
                    right_size_candidates,
                    2,
                    max_width_px=width * 0.78,
                    prefer_single_mixed_short=False,
                )
            size = min(left_size, right_size)
            lines = left_lines + right_lines
            if len(lines) <= 3:
                return lines, size + (4 if section_role == "cover" else 0)
    return _fit_text_block(
        text,
        [12, 10, 8, 7] if re.search(r"[\u4e00-\u9fff]", text) else [20, 18, 16],
        [max(60, int(width * 0.102)), max(54, int(width * 0.092)), max(46, int(width * 0.080))],
        3,
        max_width_px=width * 0.78,
        prefer_single_mixed_short=True,
    )


def _resolved_playful_controls(controls: dict[str, str]) -> tuple[str, str, str]:
    tone = controls.get("tone", "auto")
    decor_level = controls.get("decor_level", "auto")
    emoji_policy = controls.get("emoji_policy", "auto")
    if tone == "auto":
        tone = "calm"
    if decor_level == "auto":
        decor_level = "medium" if tone == "playful" else "low" if tone in {"bold", "editorial"} else "none"
    if emoji_policy == "auto":
        emoji_policy = "sparse" if tone == "playful" else "none"
    return tone, decor_level, emoji_policy


def _emoji_seed_for_text(text: str) -> str:
    lower = text.lower()
    pairs = [
        (["ai", "agent", "智能体", "模型", "harness"], "🤖"),
        (["数据", "统计", "%", "增长", "指标"], "📊"),
        (["流程", "工作流", "步骤", "flow"], "🪄"),
        (["地图", "生态", "版图", "产品"], "🗺️"),
        (["工具", "编码", "代码", "开发"], "🧰"),
        (["风险", "问题", "坑", "警惕"], "⚠️"),
        (["总结", "启示", "结论"], "✨"),
        (["支付", "钱", "成本", "credits"], "💸"),
    ]
    for needles, emoji in pairs:
        if any(token in lower for token in needles):
            return emoji
    return "✨"


def _auto_hero_emoji(text: str, tone: str = "calm") -> str:
    lower = (text or "").lower()
    pairs = [
        (["为什么", "为啥", "how", "why"], "🤔"),
        (["ai", "agent", "智能体", "harness"], "🤖"),
        (["风险", "警告", "注意", "坑"], "⚠️"),
        (["增长", "机会", "突破", "爆发"], "🚀"),
        (["方法", "步骤", "指南", "攻略"], "🧭"),
        (["工具", "产品", "地图", "生态"], "🧰"),
        (["发现", "信号", "新变化"], "💡"),
    ]
    for needles, emoji in pairs:
        if any(token in lower for token in needles):
            return emoji
    return "✨" if tone == "playful" else "💡"


def _fun_badges(copy: dict[str, Any], controls: dict[str, str], limit: int = 2) -> list[str]:
    tone, decor_level, emoji_policy = _resolved_playful_controls(controls)
    if decor_level == "none" or emoji_policy == "none":
        return []
    items: list[str] = []
    for source in [copy.get("title", ""), *(copy.get("bullets", []) or [])]:
        seed = _emoji_seed_for_text(str(source))
        if seed not in items:
            items.append(seed)
        if len(items) >= (1 if emoji_policy == "sparse" else limit):
            break
    if tone == "playful" and "🎈" not in items and emoji_policy == "expressive" and len(items) < limit:
        items.append("🎈")
    return items[:limit]


def _decor_sparkles(width: int, height: int, controls: dict[str, str], accent: str, theme_dark: bool) -> str:
    tone, decor_level, emoji_policy = _resolved_playful_controls(controls)
    if decor_level == "none" or tone not in {"playful", "bold"}:
        return ""
    opacity = "0.22" if theme_dark else "0.18"
    fill = accent if decor_level == "medium" else ("#D7DEEF" if theme_dark else "#D9DDF0")
    dots = [
        (0.88, 0.10, 0.010),
        (0.91, 0.14, 0.006),
        (0.10, 0.12, 0.008),
    ]
    parts = []
    for x, y, r in dots[: 3 if decor_level == "medium" else 2]:
        parts.append(f'<circle cx="{width*x:.2f}" cy="{height*y:.2f}" r="{width*r:.2f}" fill="{fill}" opacity="{opacity}"/>')
    if emoji_policy == "expressive":
        parts.append(_svg_text_block(width * 0.89, height * 0.18, ["✦"], max(18, int(width * 0.022)), accent, weight=800, anchor="middle"))
    return "".join(parts)


def _badge_pills_svg(
    badges: list[str],
    x: float,
    y: float,
    width: int,
    height: int,
    controls: dict[str, str],
    accent: str,
    theme_dark: bool,
) -> str:
    if not badges:
        return ""
    return ""


def _derive_info_copy(prompt: str, mode: str = "infographic") -> dict[str, Any]:
    prompt = _strip_control_directives(_strip_image_directives(prompt))
    title = _extract_labeled_value(prompt, ["标题", "主标题", "title"]) or "信息图概览"
    subtitle = _extract_labeled_value(prompt, ["副标题", "subtitle"]) or ("" if mode == "text_cover" else "清晰层级 / 重点突出 / 本地生成")
    kicker = _extract_labeled_value(prompt, ["角标", "badge"]) or ("TEXT COVER" if mode == "text_cover" else "INFOGRAPHIC")
    emphasis = _extract_labeled_value(prompt, ["核心数字", "重点数字", "highlight"]) or ""
    footer = _extract_labeled_value(prompt, ["页脚", "底部文案", "footer"]) or ""
    bullets = _parse_bullets(prompt)
    has_explicit_structure = bool(
        _extract_labeled_value(prompt, ["标题", "主标题", "title"])
        or _extract_labeled_value(prompt, ["副标题", "subtitle"])
        or bullets
    )
    if _looks_like_article_prompt(prompt) and not has_explicit_structure:
        return _derive_article_copy(prompt, mode=mode)
    if not bullets:
        bullets = ["信息层级清晰", "重点数字突出", "适合封面与知识卡片", "本地 SVG 到 PNG 导出"]
    return {
        "title": title,
        "subtitle": subtitle,
        "kicker": kicker,
        "emphasis": emphasis,
        "footer": footer,
        "bullets": bullets[:6],
    }


def _split_bullet_copy(text: str) -> tuple[str, str]:
    if "`" in text or re.search(r"[A-Za-z0-9_]+\.[A-Za-z0-9_]+", text):
        return text.strip(), "提炼重点信息，保持清晰易读。"
    if "：" in text:
        left, right = text.split("：", 1)
        return left.strip(), right.strip()
    if ":" in text:
        left, right = text.split(":", 1)
        return left.strip(), right.strip()
    compact = text.strip()
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", compact))
    has_latin = bool(re.search(r"[A-Za-z]", compact))
    if has_cjk and not has_latin and "/" not in compact and "-" not in compact:
        if len(compact) > 8:
            return compact[:6], compact[6:]
    else:
        words = compact.split()
        if len(words) > 3:
            return " ".join(words[:3]), " ".join(words[3:])
    return compact, "提炼重点信息，保持清晰易读。"


def _compact_excerpt(text: str, max_chars: int = 24) -> str:
    compact = re.sub(r"\s+", "", text).strip("，。；;：:")
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars].rstrip("，。；;：:") + "…"


def _split_qa_item(text: str) -> tuple[str, str]:
    if "：" in text or ":" in text:
        return _split_bullet_copy(text)
    compact = text.strip()
    if not compact:
        return "", ""
    # When the source is a complete statement rather than a real Q/A pair,
    # keep it intact so we don't split mixed Chinese/English phrases awkwardly.
    return compact, ""


def _extract_focus_token(text: str) -> str | None:
    latin = re.findall(r"[A-Za-z][A-Za-z0-9\-\+\.]*", text)
    if latin:
        return max(latin, key=len)
    quoted = re.findall(r"[“\"]([^”\"]+)[”\"]", text)
    if quoted:
        return quoted[0]
    return None


def _infer_infographic_kind(prompt: str) -> str:
    lower = prompt.lower()
    if any(token in lower for token in ["文章页", "article page", "正文页", "长文页"]):
        return "article_page"
    if any(token in lower for token in ["机制卡", "mechanism", "核心亮点", "关键点"]):
        return "mechanism"
    if any(token in lower for token in ["说明卡", "article note", "config note", "配置说明"]):
        return "article_note"
    if any(token in lower for token in ["文章卡", "article card", "文章排版", "长文卡片"]):
        return "article"
    if any(token in lower for token in ["清单", "checklist", "避坑", "注意事项", "升级前", "升级后", "建议"]):
        return "checklist"
    if any(token in lower for token in ["产品地图", "版图", "生态图", "landscape map", "map"]):
        return "map"
    if any(token in lower for token in ["厂家", "厂商", "工具速览", "产品速览", "目录", "速览"]):
        return "catalog"
    if any(token in lower for token in ["问答", "qa", "q&a", "问题", "解答"]):
        return "qa"
    if any(token in lower for token in ["时间线", "timeline", "演进", "历程"]):
        return "timeline"
    if any(token in lower for token in ["对比", "vs", "前后", "before", "after"]):
        return "comparison"
    if any(token in lower for token in ["流程", "步骤", "step", "配置", "自动流", "workflow"]):
        return "flow"
    if _looks_like_article_prompt(prompt) and any(token in prompt for token in ["为什么", "理由", "原因", "解读", "公告"]):
        return "mechanism"
    return "mechanism"


def _timeline_supports_text(points: list[str]) -> bool:
    if not points:
        return False
    for item in points:
        compact = re.sub(r"\s+", "", item)
        if re.search(r"[\u4e00-\u9fff]", compact):
            if len(compact) > 12:
                return False
        elif len(compact) > 20:
            return False
    return True


def _chunk_items(items: list[str], size: int) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _split_comparison_row(text: str) -> tuple[str, str, str]:
    title, rest = _split_bullet_copy(text)
    if "/" in rest:
        left, right = rest.split("/", 1)
        return title.strip(), left.strip(), right.strip()
    if "→" in rest:
        left, right = rest.split("→", 1)
        return title.strip(), left.strip(), right.strip()
    return title.strip(), rest.strip(), ""


def _split_catalog_row(text: str) -> tuple[str, str, str]:
    compact = text.strip()
    if "/" in compact:
        parts = [part.strip() for part in compact.split("/") if part.strip()]
        if len(parts) >= 3:
            return parts[0], parts[1], " / ".join(parts[2:])
        if len(parts) == 2:
            return parts[0], parts[1], ""
    if "：" in compact:
        left, right = compact.split("：", 1)
        return left.strip(), right.strip(), ""
    title, desc = _split_bullet_copy(compact)
    return title.strip(), desc.strip(), ""


def _parse_article_sections(prompt: str) -> list[dict[str, Any]]:
    lines = _meaningful_lines(prompt)
    if not lines:
        return []
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in lines[1:]:
        if _is_section_heading(line):
            if current:
                sections.append(current)
            current = {"heading": line, "lines": []}
            continue
        if current is None:
            current = {"heading": "导语", "lines": []}
        current["lines"].append(line)
    if current:
        sections.append(current)
    return sections


def _is_dense_paragraph(lines: list[str]) -> bool:
    if not lines:
        return False
    joined = " ".join(lines)
    avg_len = sum(len(line) for line in lines) / max(1, len(lines))
    punctuation = len(re.findall(r"[，。；：,:!?！？]", joined))
    has_codeish = bool(re.search(r"`[^`]+`|[A-Za-z0-9_]+\.[A-Za-z0-9_]+", joined))
    return avg_len >= 18 or punctuation >= 6 or has_codeish


def _looks_like_config_note(lines: list[str]) -> bool:
    if not lines:
        return False
    joined = " ".join(lines)
    code_hits = len(re.findall(r"`[^`]+`|[A-Za-z0-9_]+\.[A-Za-z0-9_]+", joined))
    config_words = len(re.findall(r"schema|doctor|health|gateway|plugins|plugin|feishu|lark|config|配置|字段|命令|插件", joined, flags=re.IGNORECASE))
    return code_hits >= 1 or config_words >= 3


def _merge_story_sections(sections: list[dict[str, Any]], max_sections: int = 5) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    idx = 0
    while idx < len(sections):
        section = sections[idx]
        heading = section["heading"]
        lines = list(section["lines"])
        if (
            idx + 1 < len(sections)
            and len(merged) + (len(sections) - idx) > max_sections
            and any(token in heading for token in ["坑", "问题", "建议", "配置", "插件", "Feishu", "Lark"])
        ):
            nxt = sections[idx + 1]
            if any(token in nxt["heading"] for token in ["坑", "问题", "建议", "配置", "插件", "Feishu", "Lark", "不要", "最后", "其实"]):
                heading = f"{heading} / {nxt['heading']}"
                lines.extend(nxt["lines"])
                idx += 1
        merged.append({"heading": heading, "lines": lines})
        idx += 1
    return merged


def _pick_card_heading_parts(heading: str) -> tuple[str, str]:
    parts = [part.strip() for part in heading.split("/") if part.strip()]
    if not parts:
        return heading.strip(), ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _story_card_prompt(title: str, subtitle: str, emphasis: str, bullets: list[str], heading: str) -> str:
    lower = heading.lower()
    if any(token in lower for token in ["为什么", "硬伤", "更配", "问题", "问答"]):
        parts = [
            "信息图 问答卡",
            f"角标：{heading}",
            f"标题：{title}",
            f"副标题：{subtitle}",
            f"核心数字：{emphasis}",
        ]
        for idx, item in enumerate(bullets[:4], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if any(token in lower for token in ["时间线", "演进", "历程"]):
        parts = [
            "信息图 时间线",
            f"角标：{heading}",
            f"标题：{title}",
            f"副标题：{subtitle}",
        ]
        for idx, item in enumerate(bullets[:5], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if any(token in lower for token in ["为什么", "硬伤", "更配", "公告", "数据"]):
        parts = [
            "信息图",
            f"角标：{heading}",
            f"标题：{title}",
            f"副标题：{subtitle}",
            f"核心数字：{emphasis}",
        ]
        for idx, item in enumerate(bullets[:4], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if any(token in lower for token in ["步骤", "配置", "流程"]):
        parts = [
            "信息图 流程图",
            f"角标：{heading}",
            f"标题：{title}",
            f"副标题：{subtitle}",
        ]
        for idx, item in enumerate(bullets[:5], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    return f"文字封面 标题：{title} 副标题：{subtitle} 核心数字：{emphasis}"


def _infer_section_kind(heading: str, body_lines: list[str]) -> str:
    heading_lower = heading.lower()
    joined = " ".join(body_lines).lower()
    if _looks_like_config_note(body_lines) or any(token in heading_lower for token in ["字段", "schema", "配置", "插件"]):
        return "article_page"
    if any(token in heading_lower for token in ["避坑", "建议", "提醒", "注意", "顺序"]) or any(token in joined for token in ["先", "再", "最后", "一定", "不要", "建议"]):
        return "article_page"
    if _is_dense_paragraph(body_lines):
        return "article_page"
    if any(token in heading_lower for token in ["步骤", "流程", "配置"]) or any(token in joined for token in ["step", "步骤", "流程", "然后", "接着"]):
        return "flow"
    if any(token in heading_lower for token in ["对比", "前后", "vs"]) or any(token in joined for token in ["以前", "现在", "前后", "vs", "before", "after"]):
        return "comparison"
    if any(token in heading_lower for token in ["为什么", "硬伤", "问题", "更配", "问答"]) or any(token in joined for token in ["为什么", "原因", "本质", "解读", "硬伤"]):
        return "qa"
    if any(token in heading_lower for token in ["时间线", "历程", "演进"]) or any(token in joined for token in ["发布", "随后", "后来", "至今", "阶段"]):
        return "timeline"
    if any(token in heading_lower for token in ["数据", "统计"]) or any(token in joined for token in ["万亿", "增长", "%", "倍", "指标", "调用量"]):
        return "mechanism"
    return "mechanism"


def _story_card_prompt_for_kind(title: str, subtitle: str, emphasis: str, bullets: list[str], heading: str, kind: str) -> str:
    if kind == "custom_svg":
        return f"自定义 SVG 页面 标题：{title} 副标题：{subtitle}"
    if kind == "article_page":
        parts = ["信息图 文章页", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}"]
        for idx, item in enumerate(bullets[:6], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "article_note":
        parts = ["信息图 说明卡", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}"]
        for idx, item in enumerate(bullets[:5], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "article":
        parts = ["信息图 文章卡", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}"]
        for idx, item in enumerate(bullets[:5], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "checklist":
        parts = ["信息图 清单卡", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}"]
        for idx, item in enumerate(bullets[:5], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "qa":
        parts = ["信息图 问答卡", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}", f"核心数字：{emphasis}"]
        for idx, item in enumerate(bullets[:4], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "timeline":
        parts = ["信息图 时间线", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}"]
        for idx, item in enumerate(bullets[:5], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "comparison":
        parts = ["信息图 对比图", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}"]
        for idx, item in enumerate(bullets[:5], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "catalog":
        parts = ["信息图 工具速览", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}", f"核心数字：{emphasis}"]
        for idx, item in enumerate(bullets[:6], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "map":
        parts = ["信息图 产品地图", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}", f"核心数字：{emphasis}"]
        for idx, item in enumerate(bullets[:3], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "mechanism":
        parts = ["信息图 机制卡", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}", f"核心数字：{emphasis}"]
        for idx, item in enumerate(bullets[:4], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    if kind == "flow":
        parts = ["信息图 流程图", f"角标：{heading}", f"标题：{title}", f"副标题：{subtitle}"]
        for idx, item in enumerate(bullets[:5], start=1):
            parts.append(f"{idx}. {item}")
        return " ".join(parts)
    return _story_card_prompt(title, subtitle, emphasis, bullets, heading)


def _dedupe_numbers(numbers: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in numbers:
        clean = item.replace(" ", "")
        if clean in seen:
            continue
        seen.add(clean)
        out.append(item)
    return out


def _render_outline_md(analysis: dict[str, Any]) -> str:
    lines = [
        f"# {analysis['title']}",
        "",
        f"- Strategy: {analysis['strategy']}",
        f"- Recommended card count: {analysis['recommended_card_count']}",
        f"- Key numbers: {', '.join(analysis['key_numbers']) if analysis['key_numbers'] else 'None'}",
        "",
        "## Sections",
        "",
    ]
    for idx, section in enumerate(analysis["sections"], start=1):
        lines.append(f"### {idx}. {section['heading']}")
        lines.append(f"- Kind: {section['kind']}")
        for point in section["points"]:
            lines.append(f"- {point}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_prompt_file(title: str, subtitle: str, heading: str, kind: str, prompt_text: str, bullets: list[str], emphasis: str) -> str:
    lines = [
        "---",
        f"title: {title}",
        f"heading: {heading}",
        f"kind: {kind}",
        f"subtitle: {subtitle}",
        f"emphasis: {emphasis}",
        "---",
        "",
        "## Prompt",
        "",
        prompt_text,
        "",
    ]
    if bullets:
        lines.extend(["## Points", ""])
        for item in bullets:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _story_plan_analysis(plan: dict[str, Any]) -> dict[str, Any]:
    cards = plan.get("cards", []) or []
    return {
        "title": plan.get("title", "文章图文卡组"),
        "subtitle": plan.get("subtitle", ""),
        "strategy": plan.get("strategy", "agent"),
        "recommended_card_count": len(cards),
        "section_count": len(cards),
        "key_numbers": plan.get("key_numbers", []) or [],
        "top_bullets": plan.get("top_bullets", []) or [],
        "sections": [
            {
                "heading": card.get("heading", card.get("title", f"第{i + 1}页")),
                "kind": card.get("kind", "article_page"),
                "line_count": len(card.get("bullets", []) or []),
                "points": (card.get("bullets", []) or [])[:4],
            }
            for i, card in enumerate(cards)
        ],
        "source_line_count": 0,
        "source": "agent-plan",
    }


def _validate_enum_field(errors: list[str], where: str, value: Any, allowed: set[str], field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, str) or value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        errors.append(f"{where}.{field_name} must be one of: {allowed_text}")


def _validate_story_plan(plan: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        raise ValueError("story-plan must be a JSON object")

    cards = plan.get("cards")
    if not isinstance(cards, list) or not cards:
        errors.append("story-plan.cards must be a non-empty array")
        cards = []

    for field_name, allowed in [
        ("theme", SUPPORTED_THEMES),
        ("density", SUPPORTED_DENSITIES),
        ("series_style", SUPPORTED_SERIES_STYLES),
        ("section_role", SUPPORTED_SECTION_ROLES),
        ("cover_layout", SUPPORTED_COVER_LAYOUTS),
        ("accent", SUPPORTED_ACCENTS),
        ("tone", SUPPORTED_TONES),
        ("decor_level", SUPPORTED_DECOR_LEVELS),
        ("emoji_policy", SUPPORTED_EMOJI_POLICIES),
        ("emoji_render_mode", SUPPORTED_EMOJI_RENDER_MODES),
    ]:
        _validate_enum_field(errors, "story-plan", plan.get(field_name), allowed, field_name)

    if plan.get("surface_style") is not None:
        _validate_enum_field(errors, "story-plan", plan.get("surface_style"), SUPPORTED_SURFACE_STYLES, "surface_style")
    if plan.get("style") is not None:
        _validate_enum_field(errors, "story-plan", plan.get("style"), SUPPORTED_SURFACE_STYLES, "style")

    if len(cards) > 20:
        errors.append("story-plan.cards supports at most 20 cards per render")

    for idx, card in enumerate(cards):
        where = f"story-plan.cards[{idx}]"
        if not isinstance(card, dict):
            errors.append(f"{where} must be an object")
            continue

        kind = card.get("kind", "article_page")
        if kind not in SUPPORTED_PAGE_KINDS:
            errors.append(f"{where}.kind must be one of: {', '.join(sorted(SUPPORTED_PAGE_KINDS))}")

        title = card.get("title")
        heading = card.get("heading")
        if not isinstance(title, str) and not isinstance(heading, str):
            errors.append(f"{where} should provide at least one of title or heading")

        for text_field in ["title", "heading", "subtitle", "kicker", "emphasis", "image_path", "svg_markup", "svg_path", "hero_emoji"]:
            value = card.get(text_field)
            if value is not None and not isinstance(value, str):
                errors.append(f"{where}.{text_field} must be a string when provided")

        bullets = card.get("bullets")
        if bullets is not None:
            if not isinstance(bullets, list):
                errors.append(f"{where}.bullets must be an array of strings")
            else:
                for bullet_idx, bullet in enumerate(bullets):
                    if not isinstance(bullet, str):
                        errors.append(f"{where}.bullets[{bullet_idx}] must be a string")
                if len(bullets) > 8:
                    errors.append(f"{where}.bullets should stay at 8 items or fewer for mobile readability")

        for field_name, allowed in [
            ("theme", SUPPORTED_THEMES),
            ("density", SUPPORTED_DENSITIES),
            ("series_style", SUPPORTED_SERIES_STYLES),
            ("section_role", SUPPORTED_SECTION_ROLES),
            ("cover_layout", SUPPORTED_COVER_LAYOUTS),
            ("accent", SUPPORTED_ACCENTS),
            ("tone", SUPPORTED_TONES),
            ("decor_level", SUPPORTED_DECOR_LEVELS),
            ("emoji_policy", SUPPORTED_EMOJI_POLICIES),
            ("emoji_render_mode", SUPPORTED_EMOJI_RENDER_MODES),
        ]:
            _validate_enum_field(errors, where, card.get(field_name), allowed, field_name)

        if card.get("surface_style") is not None:
            _validate_enum_field(errors, where, card.get("surface_style"), SUPPORTED_SURFACE_STYLES, "surface_style")
        if card.get("style") is not None:
            _validate_enum_field(errors, where, card.get("style"), SUPPORTED_SURFACE_STYLES, "style")
        if kind == "custom_svg" and not card.get("svg_markup") and not card.get("svg_path"):
            errors.append(f"{where} with kind=custom_svg must provide svg_markup or svg_path")

    if errors:
        details = "\n- ".join(errors[:12])
        if len(errors) > 12:
            details += f"\n- ...and {len(errors) - 12} more"
        raise ValueError(
            "story-plan validation failed:\n- "
            + details
            + f"\nSee template: {STORY_PLAN_TEMPLATE_PATH}\nSee schema: {STORY_PLAN_SCHEMA_PATH}"
        )

    return plan


def _story_plan_lints(plan: dict[str, Any]) -> list[dict[str, str]]:
    lints: list[dict[str, str]] = []
    cards = [card for card in (plan.get("cards", []) or []) if isinstance(card, dict)]
    global_theme = plan.get("theme", "auto")
    global_series_style = plan.get("series_style", "auto")
    meta_patterns = [
        "文章里",
        "文中",
        "这篇文章",
        "作者认为",
        "作者提到",
        "文中提到",
        "文章提到",
    ]

    def add(level: str, code: str, message: str) -> None:
        lints.append({"level": level, "code": code, "message": message})

    if global_series_style == "unified":
        themes = []
        for idx, card in enumerate(cards, start=1):
            theme = card.get("theme", global_theme)
            if isinstance(theme, str) and theme != "auto":
                themes.append((idx, theme, card.get("heading", card.get("title", f"第{idx}页"))))
        unique_themes = {theme for _, theme, _ in themes}
        if len(unique_themes) > 1:
            joined = ", ".join(f"{heading}:{theme}" for _, theme, heading in themes)
            add(
                "warning",
                "mixed-theme-in-unified-series",
                f"series_style=unified but pages use mixed explicit themes ({joined}). Prefer one main theme family unless the contrast is intentional.",
            )

    for idx, card in enumerate(cards, start=1):
        where = f"cards[{idx}]"
        heading = card.get("heading", card.get("title", where))
        for field in ["title", "subtitle"]:
            value = card.get(field)
            if isinstance(value, str) and any(token in value for token in meta_patterns):
                add(
                    "warning",
                    "meta-voice",
                    f"{where}.{field} contains meta phrasing ({heading}). Prefer expressing the article's idea directly instead of saying '文章里/文中/作者认为'.",
                )
        bullets = card.get("bullets", []) or []
        if isinstance(bullets, list):
            for bullet_idx, bullet in enumerate(bullets, start=1):
                if isinstance(bullet, str) and any(token in bullet for token in meta_patterns):
                    add(
                        "warning",
                        "meta-voice",
                        f"{where}.bullets[{bullet_idx}] contains meta phrasing ({heading}). Prefer direct expression over article commentary.",
                    )
        if card.get("section_role") == "summary" and card.get("image_path"):
            add(
                "warning",
                "summary-image-check",
                f"{where} is a summary page with image_path ({heading}). Double-check that the image strengthens the closing message instead of distracting from it.",
            )
        if isinstance(bullets, list) and len(bullets) >= 4 and all(isinstance(item, str) and len(_clean_line(item)) > 42 for item in bullets):
            add(
                "warning",
                "dense-bullets",
                f"{where} has several long bullets ({heading}). Consider article_page or shorter bullet rewriting for better phone readability.",
            )
    return lints


def _build_story_cards_from_plan(plan: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    analysis = _story_plan_analysis(plan)
    global_title = analysis["title"]
    global_subtitle = analysis["subtitle"] or ""
    global_theme = plan.get("theme", "auto")
    global_density = plan.get("density", "auto")
    global_series_style = plan.get("series_style", "auto")
    global_section_role = plan.get("section_role", "auto")
    global_surface_style = plan.get("surface_style", plan.get("style", "auto"))
    global_accent = plan.get("accent", "auto")
    global_tone = plan.get("tone", "auto")
    global_decor_level = plan.get("decor_level", "auto")
    global_emoji_policy = plan.get("emoji_policy", "auto")
    global_emoji_render_mode = plan.get("emoji_render_mode", "auto")
    global_cover_layout = plan.get("cover_layout", "auto")
    global_hero_emoji = plan.get("hero_emoji", "")
    cards: list[dict[str, Any]] = []
    raw_cards = plan.get("cards", []) or []
    card_index = 1

    if not raw_cards or raw_cards[0].get("kind") not in {"text_cover", "custom_svg"}:
        cover_prompt = _append_render_controls(
            f"文字封面 标题：{global_title} 副标题：{global_subtitle} 核心数字：",
            global_theme,
            global_density,
            global_surface_style,
            global_accent,
            global_series_style,
            "cover",
            global_tone,
            global_decor_level,
            global_emoji_policy,
            global_emoji_render_mode,
            global_cover_layout,
            global_hero_emoji,
        )
        cards.append(
            {
                "index": card_index,
                "heading": "cover",
                "kind": "text_cover",
                "title": global_title,
                "subtitle": global_subtitle,
                "emphasis": "",
                "bullets": [],
                "stem": "01-cover",
                "prompt": cover_prompt,
                "tone": global_tone,
                "decor_level": global_decor_level,
                "emoji_policy": global_emoji_policy,
                "emoji_render_mode": global_emoji_render_mode,
                "cover_layout": global_cover_layout,
                "hero_emoji": global_hero_emoji,
            }
        )
        card_index += 1

    for raw in raw_cards:
        kind = raw.get("kind", "article_page")
        title = raw.get("title") or raw.get("heading") or f"第{card_index}页"
        subtitle = raw.get("subtitle", "")
        heading = raw.get("heading", title)
        bullets = [str(item).strip() for item in (raw.get("bullets", []) or []) if str(item).strip()]
        emphasis = raw.get("emphasis", "")
        prompt = _story_card_prompt_for_kind(title, subtitle, emphasis, bullets, heading, kind)
        prompt = _append_render_controls(
            prompt,
            raw.get("theme", global_theme),
            raw.get("density", global_density),
            raw.get("surface_style", raw.get("style", global_surface_style)),
            raw.get("accent", global_accent),
            raw.get("series_style", global_series_style),
            raw.get("section_role", global_section_role),
            raw.get("tone", global_tone),
            raw.get("decor_level", global_decor_level),
            raw.get("emoji_policy", global_emoji_policy),
            raw.get("emoji_render_mode", global_emoji_render_mode),
            raw.get("cover_layout", global_cover_layout),
            raw.get("hero_emoji", global_hero_emoji),
        )
        if raw.get("image_path"):
            prompt = f"{prompt}\n插图文件：{raw['image_path']}"
        stem = f"{card_index:02d}-{_slugify(heading)[:24]}"
        cards.append(
            {
                "index": card_index,
                "heading": heading,
                "kind": kind,
                "title": title,
                "subtitle": subtitle,
                "emphasis": emphasis,
                "bullets": bullets[:6],
                "stem": stem,
                "prompt": prompt,
                "style": raw.get("style", ""),
                "series_style": raw.get("series_style", global_series_style),
                "section_role": raw.get("section_role", global_section_role),
                "tone": raw.get("tone", global_tone),
                "decor_level": raw.get("decor_level", global_decor_level),
                "emoji_policy": raw.get("emoji_policy", global_emoji_policy),
                "emoji_render_mode": raw.get("emoji_render_mode", global_emoji_render_mode),
                "cover_layout": raw.get("cover_layout", global_cover_layout),
                "hero_emoji": raw.get("hero_emoji", global_hero_emoji),
                "image_path": raw.get("image_path"),
                "svg_markup": raw.get("svg_markup"),
                "svg_path": raw.get("svg_path"),
            }
        )
        card_index += 1
        if card_index > 20:
            break

    return analysis, cards


def _estimate_article_point_weight(text: str) -> float:
    clean = re.sub(r"\s+", "", text)
    base = max(1.0, len(clean) / 22.0)
    if re.search(r"https?://|`[^`]+`|[A-Za-z0-9_]+\.[A-Za-z0-9_]+", text):
        base += 0.8
    if len(clean) <= 28:
        base -= 0.2
    return max(0.8, base)


def _paginate_article_points(points: list[str], max_weight: float = 8.8, max_points: int = 4) -> list[list[str]]:
    pages: list[list[str]] = []
    current: list[str] = []
    current_weight = 0.0
    for point in points:
        weight = _estimate_article_point_weight(point)
        if current and (current_weight + weight > max_weight or len(current) >= max_points):
            pages.append(current)
            current = [point]
            current_weight = weight
        else:
            current.append(point)
            current_weight += weight
    if current:
        pages.append(current)
    return pages or [points[:max_points]]


def _looks_like_feature_card_line(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    return bool(
        "——" in text
        or any(token in text for token in ["执行能力", "拥有记忆", "持续进化", "24小时", "7x24", "7 x 24"])
        or compact.startswith("「")
    )


def _plan_section_cards(heading: str, title: str, subtitle: str, section_kind: str, body_lines: list[str]) -> list[dict[str, Any]]:
    if (
        section_kind == "article_page"
        and ("什么是" in heading or "是什么" in heading)
        and len(body_lines) >= 3
    ):
        intro_lines = body_lines[:1]
        feature_lines = [line for line in body_lines[1:] if _looks_like_feature_card_line(line)]
        trailing_lines = [line for line in body_lines[1:] if line not in feature_lines]
        planned: list[dict[str, Any]] = []
        if intro_lines:
            planned.append(
                {
                    "title": title,
                    "subtitle": subtitle,
                    "kind": "article_page",
                    "bullets": intro_lines + trailing_lines[:1],
                }
            )
        if feature_lines:
            planned.append(
                {
                    "title": "OpenClaw 的 4 个核心特点",
                    "subtitle": "与传统 AI 工具不同，它更像能持续干活的智能体",
                    "kind": "mechanism",
                    "bullets": feature_lines[:4],
                }
            )
        if planned:
            return planned

    if section_kind == "article_page":
        pages = _paginate_article_points(body_lines[:8], max_weight=8.8, max_points=4)
        return [
            {
                "title": title if len(pages) == 1 else f"{title}（{idx + 1}）",
                "subtitle": subtitle if idx == 0 else f"{_compact_excerpt(page[0], max_chars=20)} · 续页",
                "kind": section_kind,
                "bullets": page[:6],
            }
            for idx, page in enumerate(pages)
        ]

    return [
        {
            "title": title,
            "subtitle": subtitle,
            "kind": section_kind,
            "bullets": body_lines[:6],
        }
    ]


def _recommend_story_strategy(prompt: str, sections: list[dict[str, Any]]) -> str:
    lower = prompt.lower()
    if any(token in lower for token in ["教程", "步骤", "配置", "怎么做", "workflow", "guide"]):
        return "dense"
    if any(token in lower for token in ["故事", "经历", "踩坑", "复盘", "分享"]):
        return "story"
    if any(token in lower for token in ["审美", "穿搭", "摄影", "氛围", "视觉"]):
        return "visual"
    if len(sections) >= 3:
        return "dense"
    return "story"


def _analyze_article(prompt: str, strategy: str = "auto") -> dict[str, Any]:
    article = _derive_article_copy(prompt, mode="infographic")
    sections = _merge_story_sections(_parse_article_sections(prompt))
    lines = _meaningful_lines(prompt)
    resolved_strategy = _recommend_story_strategy(prompt, sections) if strategy == "auto" else strategy
    key_numbers = _dedupe_numbers(re.findall(r"\d+(?:\.\d+)?\s*(?:万亿|亿|万|多倍|倍|%|年|月|日)", prompt))
    section_summaries: list[dict[str, Any]] = []
    for section in sections:
        body_lines = [line for line in section["lines"] if len(line) >= 6][:5]
        if not body_lines:
            continue
        kind = _infer_section_kind(section["heading"], body_lines)
        section_summaries.append(
            {
                "heading": section["heading"],
                "kind": kind,
                "line_count": len(section["lines"]),
                "points": body_lines[:4],
            }
        )
    return {
        "title": article["title"],
        "subtitle": article["subtitle"],
        "strategy": resolved_strategy,
        "recommended_card_count": min(max(1 + len(section_summaries), 3), 8),
        "section_count": len(section_summaries),
        "key_numbers": key_numbers[:8],
        "top_bullets": article["bullets"][:4],
        "sections": section_summaries,
        "source_line_count": len(lines),
    }


def _build_story_cards(prompt: str, strategy: str = "auto") -> tuple[dict[str, Any], list[dict[str, Any]]]:
    article = _derive_article_copy(prompt, mode="infographic")
    sections = _merge_story_sections(_parse_article_sections(prompt))
    analysis = _analyze_article(prompt, strategy=strategy)
    resolved_strategy = analysis["strategy"]
    cards: list[dict[str, Any]] = []

    cover_prompt = (
        f'文字封面 标题：{article["title"]} '
        f'副标题：{article["subtitle"]} '
        f'核心数字：{article["emphasis"]}'
    )
    cards.append(
        {
            "index": 1,
            "heading": "cover",
            "kind": "text_cover",
            "title": article["title"],
            "subtitle": article["subtitle"],
            "emphasis": article["emphasis"],
            "bullets": article["bullets"][:4],
            "stem": "01-cover",
            "prompt": cover_prompt,
        }
    )

    card_index = 2
    for section in sections:
        heading = section["heading"]
        if heading == "导语":
            continue
        body_lines = [line for line in section["lines"] if len(line) >= 6][:8]
        if not body_lines:
            continue
        heading_title, heading_sub = _pick_card_heading_parts(heading)
        title = heading_title
        subtitle = heading_sub or _compact_excerpt(body_lines[0], max_chars=24)
        emphasis = _pick_stat_phrase("\n".join([heading, *body_lines])) or article["emphasis"]
        section_kind = _infer_section_kind(heading, body_lines)
        planned_cards = _plan_section_cards(heading, title, subtitle, section_kind, body_lines)

        for page_idx, planned in enumerate(planned_cards, start=1):
            page_title = planned["title"]
            page_subtitle = planned["subtitle"]
            page_kind = planned["kind"]
            page_points = planned["bullets"]
            card_prompt = _story_card_prompt_for_kind(page_title, page_subtitle, emphasis, page_points, heading, page_kind)
            if resolved_strategy == "story" and card_index == 2:
                card_prompt = f"文字封面 标题：{page_title} 副标题：{page_subtitle} 核心数字：{emphasis}"
                page_kind = "text_cover"
            elif resolved_strategy == "visual" and any(token in heading for token in ["公告", "数据"]):
                card_prompt = f"文字封面 标题：{page_title} 副标题：{page_subtitle} 核心数字：{emphasis}"
                page_kind = "text_cover"
            stem_heading = heading if len(planned_cards) == 1 else f"{heading}-{page_idx}"
            stem = f"{card_index:02d}-{_slugify(stem_heading)[:24]}"
            cards.append(
                {
                    "index": card_index,
                    "heading": heading if len(planned_cards) == 1 else f"{heading}（{page_idx}）",
                    "kind": page_kind,
                    "title": page_title,
                    "subtitle": page_subtitle,
                    "emphasis": emphasis,
                    "bullets": page_points[:6],
                    "stem": stem,
                    "prompt": card_prompt,
                }
            )
            card_index += 1
            if card_index > 8:
                break
        if card_index > 8:
            break

    return analysis, cards


def _attach_story_images(cards: list[dict[str, Any]], image_paths: list[str]) -> None:
    if not image_paths:
        return
    targets = [card for card in cards if card["kind"] == "article_page"]
    if not targets:
        targets = [card for card in cards if card["kind"] != "text_cover"]
    for card, image_path in zip(targets, image_paths):
        card["image_path"] = image_path
        card["prompt"] = f'{card["prompt"]}\n插图文件：{image_path}'


def generate_article_story(
    prompt: str,
    output_dir: str | Path,
    width: int,
    height: int,
    strategy: str = "auto",
    mode: str = "all",
    story_images: list[str] | None = None,
    story_plan: dict[str, Any] | None = None,
    keep_svg: bool = False,
) -> dict[str, Any]:
    story_dir = Path(output_dir).expanduser().resolve()
    story_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = story_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    if story_plan:
        analysis, cards = _build_story_cards_from_plan(story_plan)
        lints = _story_plan_lints(story_plan)
    else:
        analysis, cards = _build_story_cards(prompt, strategy=strategy)
        _attach_story_images(cards, story_images or [])
        lints = []
    resolved_strategy = analysis["strategy"]
    analysis_path = story_dir / "analysis.json"
    outline_path = story_dir / "outline.md"
    plan_path = story_dir / "story-plan.json"
    lint_path = story_dir / "story-plan-lint.json"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outline_path.write_text(_render_outline_md(analysis), encoding="utf-8")
    if story_plan:
        plan_path.write_text(json.dumps(story_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        lint_path.write_text(json.dumps({"warnings": lints}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    results: list[dict[str, Any]] = []

    for card in cards:
        prompt_file = prompts_dir / f"{card['stem']}.md"
        prompt_file.write_text(
            _render_prompt_file(
                card["title"],
                card["subtitle"],
                card["heading"],
                card["kind"],
                card["prompt"],
                card["bullets"],
                card["emphasis"],
            ),
            encoding="utf-8",
        )
        card["prompt_file"] = str(prompt_file)

    if mode in {"all", "images-only"}:
        for card in cards:
            if card["kind"] == "custom_svg":
                svg_markup = card.get("svg_markup")
                if not svg_markup and card.get("svg_path"):
                    svg_markup = Path(card["svg_path"]).expanduser().read_text(encoding="utf-8")
                if not svg_markup:
                    raise ValueError(f"Card {card['stem']} is custom_svg but no svg_markup/svg_path was provided")
                results.append(
                    generate_image_from_svg_markup(
                        svg_markup,
                        story_dir / f"{card['stem']}.png",
                        width,
                        height,
                        story_dir / f"{card['stem']}.svg" if keep_svg else None,
                        keep_svg=keep_svg,
                    )
                )
                continue
            results.append(
                generate_image(
                    card["prompt"],
                    story_dir / f"{card['stem']}.png",
                    width,
                    height,
                    story_dir / f"{card['stem']}.svg" if keep_svg else None,
                    keep_svg=keep_svg,
                )
            )

    return {
        "mode": "article-story-local",
        "output_dir": str(story_dir),
        "strategy": resolved_strategy,
        "analysis": str(analysis_path),
        "outline": str(outline_path),
        "story_plan": str(plan_path) if story_plan else None,
        "story_plan_lint": str(lint_path) if story_plan else None,
        "prompts_dir": str(prompts_dir),
        "count": len(cards),
        "generated_count": len(results),
        "warnings": lints,
        "items": results,
    }


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


def _compose_text_cover_svg(prompt: str, width: int, height: int) -> str:
    copy = _derive_info_copy(prompt, mode="text_cover")
    controls = _resolve_render_controls(prompt)
    _set_current_emoji_render_mode(controls.get("emoji_render_mode", "auto"))
    seed = _stable_int(prompt)
    clean_title, trailing_title_emoji = _split_trailing_emoji(copy["title"])
    focus_token = _extract_focus_token(clean_title)
    is_tall = (height / max(width, 1)) >= 1.35
    lower_title = clean_title.lower()
    tone, _, emoji_policy = _resolved_playful_controls(controls)
    section_role = controls.get("section_role", "auto")
    cover_layout = controls.get("cover_layout", "auto")
    if cover_layout == "auto":
        cover_layout = "hero_emoji_top" if section_role == "cover" else "title_first"
    hero_emoji = (controls.get("hero_emoji") or "").strip() or _auto_hero_emoji(clean_title, tone)
    if any(token in lower_title for token in ["为什么", "为啥", "how", "why"]):
        variant = "note"
    else:
        variant = "quote" if focus_token else ("note" if seed % 2 else "quote")
    if section_role == "cover" and cover_layout == "hero_emoji_top":
        variant = "quote"

    if variant == "quote":
        series_unified = controls.get("series_style") == "unified"
        if controls["theme"] == "dark":
            bg = "#161821"
            ink = "#F3F5FF"
            accent = "#7AA2FF" if controls["accent"] in {"auto", "blue"} else "#66D39E" if controls["accent"] == "green" else "#FFB86C" if controls["accent"] == "warm" else "#F28CC8"
            soft = "#2A3146"
        else:
            bg = "#F2ECFA"
            ink = "#3E384D"
            accent = "#FFBF47" if controls["accent"] in {"auto", "warm"} else "#5B82F4" if controls["accent"] == "blue" else "#45B97C" if controls["accent"] == "green" else "#E67AB1"
            soft = "#DBCDF4"
        quote_size = max(56, int(width * 0.10))
        title_scale_bump = 4 if section_role == "cover" else 2 if section_role == "chapter" else 0
        if section_role == "cover" and cover_layout == "title_first":
            title_lines, title_size = _cover_title_lines(clean_title, width, section_role)
        elif section_role == "cover" and cover_layout == "hero_emoji_top":
            title_lines, title_size = _hero_cover_title_lines(clean_title, width)
        else:
            title_lines, title_size = _fit_text_block(
                clean_title,
                [12, 10, 8, 7] if re.search(r"[\u4e00-\u9fff]", copy["title"]) else [20, 18, 16],
                [max(60 + title_scale_bump, int(width * 0.102)), max(54 + title_scale_bump, int(width * 0.092)), max(46 + title_scale_bump, int(width * 0.080))],
                3,
                max_width_px=width * 0.78,
                prefer_single_mixed_short=True,
        )
        subtitle_lines, subtitle_size = _fit_text_block(
            copy["subtitle"],
            [20, 16, 14] if re.search(r"[\u4e00-\u9fff]", copy["subtitle"]) else [30, 26, 22],
            [max(22, int(width * 0.028)), max(20, int(width * 0.024)), max(18, int(width * 0.021))],
            2,
            max_width_px=width * 0.72,
        )
        base_x = width * 0.12
        hero_mode = section_role == "cover" and cover_layout == "hero_emoji_top"
        title_y = height * (0.50 if hero_mode else 0.36 if section_role == "cover" else 0.38 if is_tall else 0.43)
        last_line = title_lines[-1] if title_lines else ""
        last_line_width = _estimate_line_width(last_line, title_size)
        if hero_mode:
            highlight_width = min(width * 0.40, max(width * 0.18, last_line_width * 0.64))
            highlight_x = min(width * 0.80, base_x + max(last_line_width * 0.10, width * 0.06))
            highlight_y = title_y + (len(title_lines) - 1) * title_size * 1.04 - title_size * 0.22
            highlight_h = max(height * 0.024, title_size * 0.28)
        elif section_role == "cover":
            highlight_width = min(width * 0.32, max(width * 0.16, last_line_width * 0.72))
            highlight_x = min(width * 0.80, base_x + max(last_line_width * 0.18, width * 0.10))
            highlight_y = title_y + (len(title_lines) - 1) * title_size * 1.04 - title_size * 0.26
            highlight_h = max(height * 0.025, title_size * 0.30)
        else:
            highlight_width = width * (0.30 if focus_token else 0.18)
            highlight_x = width * 0.40
            highlight_y = height * (0.395 if is_tall else 0.445)
            highlight_h = height * 0.028
        subtitle_y = min(height * 0.84, title_y + _text_block_height(title_lines, title_size, 1.04) + (height * (0.08 if hero_mode else 0.12 if series_unified else 0.10)))
        sparkles = _decor_sparkles(width, height, controls, accent, controls["theme"] == "dark")
        hero_svg = ""
        quote_marks_svg = ""
        if hero_mode:
            hero_size = max(232, int(width * 0.30))
            hero_y = height * 0.29
            hero_svg = _svg_text_block(width * 0.50, hero_y, [hero_emoji], hero_size, accent, weight=800, anchor="middle")
        else:
            quote_marks_svg = (
                f'<text x="{width*0.10:.2f}" y="{height*(0.14 if series_unified else 0.16):.2f}" font-family="Georgia, Times New Roman, serif" '
                f'font-size="{quote_size}" font-weight="900" fill="{soft}" opacity="0.8">“</text>'
                f'<text x="{width*0.16:.2f}" y="{height*(0.14 if series_unified else 0.16):.2f}" font-family="Georgia, Times New Roman, serif" '
                f'font-size="{quote_size}" font-weight="900" fill="{soft}" opacity="0.8">“</text>'
            )
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{bg}"/>
  {sparkles}
  {quote_marks_svg}
  {hero_svg}
  <rect x="{highlight_x:.2f}" y="{highlight_y:.2f}" width="{highlight_width:.2f}" height="{highlight_h:.2f}" rx="{highlight_h*0.15:.2f}" fill="{accent}"/>
  {_svg_text_block(base_x, title_y, title_lines, title_size, ink, weight=900, line_gap=1.04)}
  {_title_emoji_svg(base_x, title_y, title_lines, title_size, trailing_title_emoji, width, accent, scale=1.7 if hero_mode else 2.35 if section_role == "cover" else 1.9)}
  {_svg_text_block(base_x, subtitle_y, subtitle_lines[:2], subtitle_size, "#7A738B", weight=620, line_gap=1.20)}
</svg>'''

    if controls["theme"] == "dark":
        card_bg = "#1E2740"
        paper = "#10141F"
        shadow = "#2D3A5F"
        ink = "#F6F7FB"
        meta = "#87A3FF"
    else:
        card_bg = "#5B82F4"
        paper = "#FFFDF8"
        shadow = "#C7D5FF"
        ink = "#121212"
        meta = "#5B82F4"
    emoji = "🤔" if "为什么" in copy["title"] or "为啥" in copy["title"] else ("🫧" if tone == "playful" and emoji_policy != "none" else "...")
    paper_x = width * 0.08
    paper_y = height * 0.08
    paper_w = width * 0.84
    paper_h = height * 0.84
    title_lines, title_size = _fit_text_block(
        clean_title,
        [12, 10, 8] if re.search(r"[\u4e00-\u9fff]", copy["title"]) else [18, 16, 14],
        [max(48, int(width*(0.102 if is_tall else 0.092))), max(42, int(width*(0.09 if is_tall else 0.082))), max(36, int(width*0.074))],
        4,
        max_width_px=width * 0.70,
        prefer_single_mixed_short=True,
    )
    title_y = height*(0.38 if is_tall else 0.44)
    accent_swirl = _decor_sparkles(width, height, controls, meta, controls["theme"] == "dark")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{card_bg}"/>
  {accent_swirl}
  <rect x="{paper_x + width*0.03:.2f}" y="{paper_y - height*0.01:.2f}" width="{paper_w:.2f}" height="{paper_h:.2f}" rx="{width*0.05:.2f}" fill="{shadow}"/>
  <rect x="{paper_x:.2f}" y="{paper_y:.2f}" width="{paper_w:.2f}" height="{paper_h:.2f}" rx="{width*0.05:.2f}" fill="{paper}"/>
  {_svg_text_block(width*0.16, height*0.16, [emoji], max(34, int(width*0.07)), ink, weight=700)}
  {_svg_text_block(width*0.18, height*0.20, ["..."], max(18, int(width*0.03)), meta, weight=800)}
  {_svg_text_block(width*0.72, height*0.18, [copy["kicker"].title() if copy["kicker"] else "Text Note"], max(16, int(width*0.026)), meta, weight=800)}
  {_svg_text_block(width*0.14, title_y, title_lines, title_size, ink, weight=900, line_gap=1.08)}
  {_title_emoji_svg(width*0.14, title_y, title_lines, title_size, trailing_title_emoji, width, meta, scale=2.2)}
  <path d="M {width*0.14:.2f} {height*0.86:.2f} L {width*0.82:.2f} {height*0.86:.2f}" stroke="{meta}" stroke-width="{max(3, int(width*0.0025))}"/>
</svg>'''


def _compose_infographic_svg(prompt: str, width: int, height: int) -> str:
    image_paths = _extract_story_image_paths(prompt)
    copy = _derive_info_copy(prompt, mode="infographic")
    controls = _resolve_render_controls(prompt)
    _set_current_emoji_render_mode(controls.get("emoji_render_mode", "auto"))
    kind = _infer_infographic_kind(_strip_image_directives(prompt))
    clean_title, trailing_title_emoji = _split_trailing_emoji(copy["title"])
    title_lines, title_size = _fit_text_block(
        clean_title,
        [16, 14, 12] if re.search(r"[\u4e00-\u9fff]", copy["title"]) else [24, 22, 20],
        [max(44, int(width*0.064)), max(38, int(width*0.056)), max(32, int(width*0.048))],
        3,
        max_width_px=width * 0.88,
        prefer_single_mixed_short=True,
    )
    subtitle_lines, subtitle_size = _fit_text_block(
        copy["subtitle"],
        [24, 22, 20] if re.search(r"[\u4e00-\u9fff]", copy["subtitle"]) else [36, 32, 28],
        [max(22, int(width*0.027)), max(20, int(width*0.024)), max(18, int(width*0.022))],
        2,
        max_width_px=width * 0.86,
    )
    bullets = copy["bullets"][:]

    if kind == "article_page":
        theme_dark = controls["theme"] == "dark"
        comfy = controls["density"] != "compact"
        accent = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
        series_unified = controls.get("series_style") == "unified"
        section_role = controls.get("section_role", "auto")
        kicker_text = _visible_kicker(copy)
        sparkles = _decor_sparkles(width, height, controls, accent, theme_dark)
        paragraphs = bullets[:6] or ["把原文段落按正常文章方式排版，优先保证阅读流畅。"]
        body_top = height * 0.15
        kicker_size = max(14, int(width * 0.016))
        title_boost = 5 if section_role == "chapter" else 2 if section_role == "summary" else 0
        title_lines, title_size = _fit_text_block(
            clean_title,
            [18, 16, 14] if re.search(r"[\u4e00-\u9fff]", copy["title"]) else [24, 22, 20],
            [max(40 + title_boost, int(width*0.052)), max(34 + title_boost, int(width*0.046)), max(30 + title_boost, int(width*0.042))],
            3,
            max_width_px=width * 0.82,
            prefer_single_mixed_short=True,
        )
        subtitle_lines, subtitle_size = _fit_text_block(
            copy["subtitle"],
            [22, 20, 18] if re.search(r"[\u4e00-\u9fff]", copy["subtitle"]) else [30, 26, 24],
            [max(20, int(width*0.024)), max(18, int(width*0.022)), max(16, int(width*0.020))],
            2,
            max_width_px=width * 0.82,
        )
        title_y = body_top
        subtitle_y = title_y + _text_block_height(title_lines, title_size, 1.08) + (height * 0.024 if series_unified else height * 0.026)
        accent_rule_y = subtitle_y + _text_block_height(subtitle_lines, subtitle_size, 1.10) + (height * 0.026 if section_role == "chapter" else height * 0.022)
        paper_top = accent_rule_y + (height * 0.038 if section_role == "chapter" else height * 0.03)
        paper_h = height - paper_top - height * 0.05
        text_x = width * 0.12
        text_w = width * 0.80
        visual_y = paper_top + height * 0.03
        visual_h = 0.0
        has_visual = bool(image_paths) or any(
            re.search(r"`[^`]+`|[A-Za-z0-9_]+\.[A-Za-z0-9_]+|github|plugin|codex|claude", p, flags=re.IGNORECASE)
            for p in paragraphs
        )
        if has_visual:
            visual_h = min(height * 0.24, paper_h * 0.30)
        blocks: list[str] = [
            f'<rect x="{width*0.06:.2f}" y="{paper_top:.2f}" width="{width*0.88:.2f}" height="{paper_h:.2f}" rx="28" fill="{"#171C28" if theme_dark else "#FFFDF9"}"/>'
        ]
        if has_visual:
            card_x = width * 0.14
            card_w = width * 0.64
            image_uri = _image_data_uri(image_paths[0]) if image_paths else None
            if image_uri:
                blocks.append(f'<clipPath id="articleClip"><rect x="{card_x:.2f}" y="{visual_y:.2f}" width="{card_w:.2f}" height="{visual_h:.2f}" rx="18"/></clipPath>')
                blocks.append(f'<rect x="{card_x:.2f}" y="{visual_y:.2f}" width="{card_w:.2f}" height="{visual_h:.2f}" rx="18" fill="{"#202636" if theme_dark else "#F7F7FA"}"/>')
                blocks.append(f'<image href="{image_uri}" x="{card_x:.2f}" y="{visual_y:.2f}" width="{card_w:.2f}" height="{visual_h:.2f}" preserveAspectRatio="xMidYMid meet" clip-path="url(#articleClip)"/>')
            else:
                blocks.append(f'<rect x="{card_x:.2f}" y="{visual_y:.2f}" width="{card_w:.2f}" height="{visual_h:.2f}" rx="18" fill="#151722"/>')
                blocks.append(f'<rect x="{card_x:.2f}" y="{visual_y:.2f}" width="{card_w:.2f}" height="{visual_h*0.18:.2f}" rx="18" fill="#23263A"/>')
                blocks.append(f'<circle cx="{card_x + card_w*0.08:.2f}" cy="{visual_y + visual_h*0.09:.2f}" r="{width*0.010:.2f}" fill="#FF7A7A"/>')
                blocks.append(f'<circle cx="{card_x + card_w*0.13:.2f}" cy="{visual_y + visual_h*0.09:.2f}" r="{width*0.010:.2f}" fill="#FFC857"/>')
                blocks.append(f'<circle cx="{card_x + card_w*0.18:.2f}" cy="{visual_y + visual_h*0.09:.2f}" r="{width*0.010:.2f}" fill="#43E39B"/>')
                blocks.append(_svg_text_block(card_x + card_w*0.06, visual_y + visual_h*0.15, ["OpenClaw / Config / Plugin Note"], max(13, int(width*0.014)), "#F4F6FF", weight=700))
                for idx in range(4):
                    line_y = visual_y + visual_h*0.30 + idx * visual_h*0.13
                    blocks.append(f'<rect x="{card_x + card_w*0.07:.2f}" y="{line_y:.2f}" width="{card_w*(0.72 - idx*0.08):.2f}" height="{visual_h*0.06:.2f}" rx="8" fill="#8F99FF" fill-opacity="{0.75 - idx*0.10:.2f}"/>')
            blocks.append(f'<rect x="{card_x:.2f}" y="{visual_y + visual_h + height*0.014:.2f}" width="{card_w:.2f}" height="{height*0.0025:.2f}" rx="2" fill="{"#30384A" if theme_dark else "#ECE7DD"}"/>')
        current_y = visual_y + visual_h + (height * 0.04 if has_visual else height * 0.03)
        for idx, para in enumerate(paragraphs):
            code_like = bool(re.search(r"`[^`]+`|[A-Za-z0-9_]+\.[A-Za-z0-9_]+|https?://", para))
            chinese_wraps, latin_wraps, size_candidates, width_factor = _article_body_wrap_profile(para)
            line_gap, para_gap = _article_paragraph_rhythm(para, height, code_like=code_like)
            if controls["density"] == "compact":
                line_gap = max(1.08, line_gap - 0.10)
                para_gap *= 0.84
            elif controls["density"] == "comfy":
                line_gap += 0.06
                para_gap *= 1.10
            scaled_sizes = [
                max(size_candidates[0], int(width * 0.028)),
                max(size_candidates[1], int(width * 0.026)),
                max(size_candidates[2], int(width * 0.024)),
            ] if not code_like else [
                max(size_candidates[0], int(width * 0.020)),
                max(size_candidates[1], int(width * 0.018)),
                max(size_candidates[2], int(width * 0.017)),
            ]
            max_lines = 3 if code_like else 4
            p_lines, p_size = _fit_body_block(
                para,
                max_width_px=text_w * width_factor,
                chinese_wraps=chinese_wraps,
                latin_wraps=latin_wraps,
                size_candidates=scaled_sizes,
                max_lines=max_lines,
            )
            if code_like:
                p_h = _text_block_height(p_lines, p_size, line_gap) + height * 0.05
                blocks.append(f'<rect x="{text_x:.2f}" y="{current_y:.2f}" width="{text_w:.2f}" height="{p_h:.2f}" rx="16" fill="{"#2C2430" if theme_dark else "#FFF7E8"}"/>')
                blocks.append(_svg_text_block(text_x + width*0.03, current_y + height*0.035, p_lines, p_size, "#EBCFA0" if theme_dark else "#7B5B16", weight=680, line_gap=line_gap))
            else:
                p_h = _text_block_height(p_lines, p_size, line_gap)
                body_color = "#D9E1F0" if theme_dark else "#6A5A3E"
                body_weight = 500 if section_role == "chapter" else 470
                blocks.append(_svg_text_block(text_x, current_y + p_size, p_lines, p_size, body_color, weight=body_weight, line_gap=line_gap + 0.02))
            current_y += p_h + para_gap
            if current_y > paper_top + paper_h - height * 0.08:
                break
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0F1320" if theme_dark else "#F8F6F1"}"/>
  {sparkles}
  {_svg_text_block(width*0.12, height*0.10, [kicker_text], kicker_size, "#7F8AA3" if theme_dark else "#B3A79A", weight=700) if kicker_text else ''}
  {_svg_text_block(width*0.12, title_y, title_lines, title_size, "#F4F7FF" if theme_dark else "#6A531D", weight=900, line_gap=1.06)}
  {_title_emoji_svg(width*0.12, title_y, title_lines, title_size, trailing_title_emoji, width, accent if not theme_dark else "#BFD0FF", scale=1.9 if section_role == "chapter" else 1.7)}
  {_svg_text_block(width*0.12, subtitle_y, subtitle_lines, subtitle_size, "#B4BED4" if theme_dark else "#8F8779", weight=700, line_gap=1.10)}
  <rect x="{width*0.12:.2f}" y="{accent_rule_y:.2f}" width="{width*(0.17 if section_role == "chapter" else 0.14):.2f}" height="{height*(0.007 if series_unified else 0.006):.2f}" rx="{height*0.003:.2f}" fill="{accent if not theme_dark else "#33415D"}"/>
  <g>{''.join(blocks)}</g>
  <rect x="0" y="{height*0.985:.2f}" width="{width}" height="{height*0.015:.2f}" fill="{accent if not theme_dark else "#1E2638"}"/>
</svg>'''

    if kind == "article_note":
        theme_dark = controls["theme"] == "dark"
        accent = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
        kicker_text = _visible_kicker(copy)
        footer_lines = _footer_lines(copy)
        notes = bullets[:5] or ["保留关键字段与命令，再给出简短说明。"]
        title_y = height * 0.15
        subtitle_y = title_y + _text_block_height(title_lines, title_size, 1.04) + height * 0.026
        note_top = subtitle_y + _text_block_height(subtitle_lines[:2], subtitle_size, 1.08) + height * 0.04
        min_row_h = height * (0.095 if controls["density"] == "compact" else 0.11 if controls["density"] == "comfy" else 0.10)
        row_h, row_gap = _tight_row_metrics(height, note_top, min_row_h, len(notes))
        blocks: list[str] = []
        for idx, note in enumerate(notes):
            y = note_top + idx * (row_h + row_gap)
            head, desc = _split_bullet_copy(note)
            if desc == "提炼重点信息，保持清晰易读。":
                desc = "关键配置或命令，建议原样保留。"
            code_like = bool(re.search(r"`[^`]+`|[A-Za-z0-9_]+\.[A-Za-z0-9_]+", note))
            head_lines, head_size = _fit_body_block(
                head,
                max_width_px=width * 0.60,
                chinese_wraps=[24, 22, 20],
                latin_wraps=[34, 30, 26],
                size_candidates=[
                    max(24 if controls["density"] != "compact" else 22, int(width*0.030)),
                    max(20, int(width*0.026)),
                    max(18, int(width*0.024)),
                ],
                max_lines=2,
            )
            desc_lines, desc_size = _fit_body_block(
                desc,
                max_width_px=width * 0.58,
                chinese_wraps=[28, 24, 22],
                latin_wraps=[42, 36, 32],
                size_candidates=[
                    max(17 if controls["density"] == "comfy" else 16, int(width*0.021)),
                    max(15, int(width*0.018)),
                    max(14, int(width*0.017)),
                ],
                max_lines=2,
            )
            blocks.append(f'<rect x="{width*0.08:.2f}" y="{y:.2f}" width="{width*0.84:.2f}" height="{row_h:.2f}" rx="20" fill="{"#161D2A" if theme_dark else "#FFFFFF"}"/>')
            blocks.append(f'<rect x="{width*0.10:.2f}" y="{y + row_h*0.18:.2f}" width="{width*0.010:.2f}" height="{row_h*0.56:.2f}" rx="7" fill="{(accent if not theme_dark else "#4867A8") if code_like else ("#2A3B5A" if theme_dark else "#D9DEFF")}"/>')
            if code_like:
                blocks.append(f'<rect x="{width*0.16:.2f}" y="{y + row_h*0.16:.2f}" width="{width*0.52:.2f}" height="{height*0.030:.2f}" rx="12" fill="{"#1D2638" if theme_dark else "#F5F1FF"}"/>')
                blocks.append(_svg_text_block(width*0.18, y + row_h*0.16 + height*0.021, head_lines, max(16, head_size-2), accent if not theme_dark else "#D6C6FF", weight=900, line_gap=1.02))
                blocks.append(_svg_text_block(width*0.16, y + row_h*0.56, desc_lines, desc_size, "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.08))
            else:
                blocks.append(_svg_text_block(width*0.16, y + row_h*0.36, head_lines, head_size, "#F4F7FF" if theme_dark else "#243047", weight=820, line_gap=1.05))
                blocks.append(_svg_text_block(width*0.16, y + row_h*0.64, desc_lines, desc_size, "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.08))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0F1320" if theme_dark else "#F5F6FC"}"/>
  {f'<rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.22:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="{"#1A2234" if theme_dark else "#EEF2FF"}"/>{_svg_text_block(width*0.10, height*0.105, [kicker_text], max(14, int(width*0.017)), accent if not theme_dark else "#BFD0FF", weight=800)}' if kicker_text else ''}
  {_svg_text_block(width*0.07, title_y, title_lines, title_size, "#F4F7FF" if theme_dark else "#243047", weight=900, line_gap=1.05)}
  {_svg_text_block(width*0.07, subtitle_y, subtitle_lines[:2], subtitle_size, "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.08)}
  <g>{''.join(blocks)}</g>
  {_svg_text_block(width*0.50, height*0.95, footer_lines, max(14, int(width*0.018)), "#8F99AF" if theme_dark else "#A7ADBF", weight=600, anchor="middle") if footer_lines else ''}
</svg>'''

    if kind == "article":
        paragraphs = bullets[:5] or ["把大段内容按正常文章方式排开，优先保证阅读流畅。"]
        kicker_text = _visible_kicker(copy)
        footer_lines = _footer_lines(copy)
        title_y = height * 0.15
        subtitle_y = title_y + _text_block_height(title_lines, title_size, 1.04) + height * 0.026
        kicker_y = subtitle_y + _text_block_height(subtitle_lines[:2], subtitle_size, 1.08) + height * 0.028
        paper_y = kicker_y + height * 0.04
        paper_h = height - paper_y - height * 0.08
        para_gap = height * 0.026
        paragraph_h = (paper_h - para_gap * (len(paragraphs) - 1) - height * 0.06) / max(1, len(paragraphs))
        body: list[str] = [
            f'<rect x="{width*0.07:.2f}" y="{paper_y:.2f}" width="{width*0.86:.2f}" height="{paper_h:.2f}" rx="28" fill="#FFFFFF"/>'
        ]
        for idx, paragraph in enumerate(paragraphs):
            y = paper_y + height * 0.04 + idx * (paragraph_h + para_gap)
            lines, size = _fit_body_block(
                paragraph,
                max_width_px=width * 0.72,
                chinese_wraps=[26, 24, 22],
                latin_wraps=[38, 34, 30],
                size_candidates=[max(23, int(width*0.028)), max(21, int(width*0.026)), max(19, int(width*0.024))],
                max_lines=3,
            )
            body.append(f'<rect x="{width*0.11:.2f}" y="{y - paragraph_h*0.10:.2f}" width="{width*0.78:.2f}" height="{paragraph_h:.2f}" rx="18" fill="#F7F8FC"/>')
            body.append(f'<rect x="{width*0.13:.2f}" y="{y + paragraph_h*0.10:.2f}" width="{width*0.010:.2f}" height="{paragraph_h*0.45:.2f}" rx="7" fill="#D9DEFF"/>')
            body.append(_svg_text_block(width*0.17, y + paragraph_h*0.22, lines, size, "#394156", weight=760, line_gap=1.12))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#F5F6FC"/>
  {f'<rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.22:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="#EEF2FF"/>{_svg_text_block(width*0.10, height*0.105, [kicker_text], max(14, int(width*0.017)), "#6B74D8", weight=800)}' if kicker_text else ''}
  {_svg_text_block(width*0.07, title_y, title_lines, title_size, "#243047", weight=900, line_gap=1.05)}
  {_svg_text_block(width*0.07, subtitle_y, subtitle_lines[:2], subtitle_size, "#7E869B", weight=700, line_gap=1.08)}
  {f'<rect x="{width*0.07:.2f}" y="{kicker_y:.2f}" width="{width*0.12:.2f}" height="{height*0.04:.2f}" rx="16" fill="#F2EEFF"/>{_svg_text_block(width*0.10, kicker_y + height*0.026, [copy["emphasis"]], max(18, int(width*0.022)), "#7A59E6", weight=900)}' if copy["emphasis"] else ''}
  <g>{''.join(body)}</g>
  {_svg_text_block(width*0.50, height*0.95, footer_lines, max(14, int(width*0.018)), "#A7ADBF", weight=600, anchor="middle") if footer_lines else ''}
</svg>'''

    if kind == "checklist":
        theme_dark = controls["theme"] == "dark"
        accent = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
        section_role = controls.get("section_role", "auto")
        kicker_text = _visible_kicker(copy)
        footer_lines = _footer_lines(copy)
        items = bullets[:5] or ["升级前先备份配置", "先跑 doctor", "确认插件来源", "最后再恢复渠道配置"]
        sparkles = _decor_sparkles(width, height, controls, accent, theme_dark)
        tone, _, emoji_policy = _resolved_playful_controls(controls)
        title_y = height * 0.15
        subtitle_y = title_y + _text_block_height(title_lines, title_size, 1.04) + height * 0.024
        badge_y = subtitle_y + _text_block_height(subtitle_lines[:2], subtitle_size, 1.08) + height * 0.028
        list_top = badge_y + (height * 0.062 if section_role == "summary" else height * 0.056)
        min_row_h = height * (0.095 if controls["density"] == "compact" else 0.11 if controls["density"] == "comfy" else 0.10)
        row_h, row_gap = _tight_row_metrics(height, list_top, min_row_h, len(items))
        checks: list[str] = []
        colors = [
            accent,
            "#F06AB2" if accent != "#D96DB4" else "#5B82F4",
            "#35C5F2" if accent != "#5B82F4" else "#45B97C",
            "#43E39B" if accent != "#45B97C" else "#E67E22",
            "#FFB84D" if accent != "#E67E22" else "#D96DB4",
        ]
        for idx, item in enumerate(items):
            y = list_top + idx * (row_h + row_gap)
            lines, size = _fit_body_block(
                item,
                max_width_px=width * 0.62,
                chinese_wraps=[24, 22, 20],
                latin_wraps=[34, 30, 26],
                size_candidates=[
                    max(24 if controls["density"] != "compact" else 22, int(width*0.030)),
                    max(21 if controls["density"] == "comfy" else 20, int(width*0.027)),
                    max(18, int(width*0.024)),
                ],
                max_lines=2,
            )
            checks.append(f'<rect x="{width*0.08:.2f}" y="{y:.2f}" width="{width*0.84:.2f}" height="{row_h:.2f}" rx="20" fill="{"#161D2A" if theme_dark else "#FFFFFF"}"/>')
            marker = "✅" if tone == "playful" and emoji_policy != "none" else "✓"
            marker_color = colors[idx % len(colors)] if marker == "✓" else None
            checks.append(_svg_text_block(width*0.14, y + row_h*0.48, [marker], max(30, int(width*0.036)) if marker != "✓" else max(22, int(width*0.026)), marker_color or "#111111", weight=900, anchor="middle"))
            checks.append(_svg_text_block(width*0.20, y + row_h*0.42, lines, size, "#EFF3FF" if theme_dark else "#2A2F45", weight=820, line_gap=1.08))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0F1320" if theme_dark else "#F5F6FC"}"/>
  {sparkles}
  {f'<rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.24:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="{"#1A2234" if theme_dark else "#EEF2FF"}"/>{_svg_text_block(width*0.10, height*0.105, [kicker_text], max(14, int(width*0.017)), accent if not theme_dark else "#BFD0FF", weight=800)}' if kicker_text else ''}
  {_svg_text_block(width*0.07, title_y, title_lines, title_size, "#F4F7FF" if theme_dark else "#243047", weight=900, line_gap=1.05)}
  {_title_emoji_svg(width*0.07, title_y, title_lines, title_size, trailing_title_emoji, width, accent if not theme_dark else "#BFD0FF", scale=1.75)}
  {_svg_text_block(width*0.07, subtitle_y, subtitle_lines[:2], subtitle_size, "#B7C0D5" if theme_dark else "#7E869B", weight=700, line_gap=1.08)}
  {f'<rect x="{width*0.07:.2f}" y="{badge_y:.2f}" width="{width*0.14:.2f}" height="{height*0.04:.2f}" rx="16" fill="{"#1C2538" if theme_dark else "#F2EEFF"}"/>{_svg_text_block(width*0.10, badge_y + height*0.026, [copy["emphasis"]], max(18, int(width*0.022)), accent if not theme_dark else "#D3BEFF", weight=900)}' if copy["emphasis"] else ''}
  <g>{''.join(checks)}</g>
  {_svg_text_block(width*0.50, height*0.95, footer_lines, max(14, int(width*0.018)), "#8F99AF" if theme_dark else "#A7ADBF", weight=600, anchor="middle") if footer_lines else ''}
</svg>'''

    if kind == "map":
        theme_dark = controls["theme"] == "dark"
        accent_base = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
        series_unified = controls.get("series_style") == "unified"
        section_role = controls.get("section_role", "auto")
        kicker_text = _visible_kicker(copy)
        footer_lines = _footer_lines(copy)
        zones = bullets[:3] or [
            "编码代理：Claude Code、Codex、Gemini CLI，强调终端执行与代理能力",
            "AI IDE：Cursor、Windsurf、GitHub Copilot，强调上下文与协作",
            "云端开发与应用生成：Replit、Lovable、Bolt.new，强调原型与部署",
        ]
        role_title_bump = 5 if section_role == "chapter" else 2 if section_role == "summary" else 0
        map_title_size = title_size + role_title_bump
        title_y = height * (0.14 if section_role == "chapter" else 0.15)
        subtitle_y = title_y + _text_block_height(title_lines, map_title_size, 1.04) + (height * 0.03 if section_role == "chapter" else height * 0.028)
        subtitle_gap = height * (0.03 if series_unified else 0.028)
        badge_y = subtitle_y + _text_block_height(subtitle_lines[:2], subtitle_size, 1.08) + subtitle_gap
        zone_top = badge_y + (height * 0.055 if section_role == "chapter" else height * 0.05)
        zone_gap = height * (0.03 if series_unified else 0.035)
        available_h = height - zone_top - height * 0.12 - zone_gap * max(0, len(zones) - 1)
        colors = [
            (("#18243B" if theme_dark else "#EAF0FF"), accent_base),
            (("#2A1E39" if theme_dark else "#F8EEFF"), "#C75BCE" if accent_base != "#D96DB4" else "#5B82F4"),
            (("#162D28" if theme_dark else "#ECFFF5"), "#32A56A" if accent_base != "#45B97C" else "#E67E22"),
        ]
        zone_specs: list[tuple[list[str], int, list[str], int]] = []
        desired_heights: list[float] = []
        min_zone_h = height * 0.18
        blocks: list[str] = []
        for item in zones:
            heading, desc = _split_bullet_copy(item)
            heading_lines, heading_size = _fit_body_block(
                heading,
                max_width_px=width * 0.64,
                chinese_wraps=[16, 14, 12],
                latin_wraps=[26, 22, 18],
                size_candidates=[
                    max(30 if controls["density"] != "compact" else 28, int(width*0.036)),
                    max(24, int(width*0.030)),
                    max(20, int(width*0.026)),
                ],
                max_lines=2,
            )
            desc_lines, desc_size = _fit_body_block(
                desc,
                max_width_px=width * 0.66,
                chinese_wraps=[40, 36, 32],
                latin_wraps=[56, 48, 42],
                size_candidates=[
                    max(20 if controls["density"] == "comfy" else 19, int(width*0.024)),
                    max(17, int(width*0.021)),
                    max(15, int(width*0.019)),
                ],
                max_lines=3,
            )
            heading_h = _text_block_height(heading_lines, heading_size, 1.05)
            desc_h = _text_block_height(desc_lines, desc_size, 1.08)
            desired_heights.append(max(min_zone_h, height * 0.09 + heading_h + desc_h + height * 0.09))
            zone_specs.append((heading_lines, heading_size, desc_lines, desc_size))
        total_desired = sum(desired_heights)
        if total_desired <= available_h:
            zone_heights = desired_heights
        else:
            scale = available_h / total_desired
            zone_heights = [max(min_zone_h * 0.92, h * scale) for h in desired_heights]
            diff = available_h - sum(zone_heights)
            if zone_heights:
                zone_heights[-1] += diff
        current_y = zone_top
        for idx, item in enumerate(zones):
            heading, desc = _split_bullet_copy(item)
            heading_lines, heading_size, desc_lines, desc_size = zone_specs[idx]
            zone_h = zone_heights[idx]
            y = current_y
            current_y += zone_h + zone_gap
            bg_fill, zone_accent = colors[idx % len(colors)]
            heading_y = y + zone_h * 0.24
            desc_y = heading_y + _text_block_height(heading_lines, heading_size, 1.05) + max(height * 0.022, zone_h * 0.11)
            max_desc_y = y + zone_h - max(height * 0.05, zone_h * 0.18)
            if desc_y > max_desc_y:
                desc_y = max_desc_y
            blocks.append(f'<rect x="{width*0.08:.2f}" y="{y:.2f}" width="{width*0.84:.2f}" height="{zone_h:.2f}" rx="24" fill="{bg_fill}"/>')
            blocks.append(f'<rect x="{width*0.10:.2f}" y="{y + zone_h*0.18:.2f}" width="{width*0.012:.2f}" height="{zone_h*0.62:.2f}" rx="8" fill="{zone_accent}"/>')
            blocks.append(_svg_text_block(width*0.15, heading_y, heading_lines, heading_size, "#F4F7FF" if theme_dark else "#243047", weight=900, line_gap=1.05))
            blocks.append(_svg_text_block(width*0.15, desc_y, desc_lines, desc_size, "#A6B0C5" if theme_dark else "#667089", weight=700, line_gap=1.08))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0F1320" if theme_dark else "#F5F6FC"}"/>
  {f'<rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.24:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="{"#1A2234" if theme_dark else "#EEF2FF"}"/>{_svg_text_block(width*0.10, height*0.105, [kicker_text], max(14, int(width*0.017)), accent_base if not theme_dark else "#BFD0FF", weight=800)}' if kicker_text else ''}
  {_svg_text_block(width*0.08, title_y, title_lines, map_title_size, "#F4F7FF" if theme_dark else "#243047", weight=900, line_gap=1.04)}
  {_svg_text_block(width*0.08, subtitle_y, subtitle_lines[:2], subtitle_size, "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.08)}
  {f'<rect x="{width*0.08:.2f}" y="{badge_y:.2f}" width="{width*0.12:.2f}" height="{height*0.04:.2f}" rx="16" fill="{"#1C2538" if theme_dark else "#F2EEFF"}"/>{_svg_text_block(width*0.11, badge_y + height*0.026, [copy["emphasis"]], max(18, int(width*0.022)), accent_base if not theme_dark else "#D3BEFF", weight=900)}' if copy["emphasis"] else ''}
  <g>{''.join(blocks)}</g>
  {_svg_text_block(width*0.50, height*0.94, footer_lines, max(14, int(width*0.018)), "#8F99AF" if theme_dark else "#A7ADBF", weight=600, anchor="middle") if footer_lines else ''}
</svg>'''

    if kind == "catalog":
        theme_dark = controls["theme"] == "dark"
        accent = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
        series_unified = controls.get("series_style") == "unified"
        section_role = controls.get("section_role", "auto")
        kicker_text = _visible_kicker(copy)
        footer_lines = _footer_lines(copy)
        sparkles = _decor_sparkles(width, height, controls, accent, theme_dark)
        mixed_title = bool(re.search(r"[\u4e00-\u9fff]", copy["title"]) and re.search(r"[A-Za-z]", copy["title"]))
        compact_title = re.sub(r"\s+", "", copy["title"])
        if mixed_title and len(compact_title) <= 20:
            catalog_title_lines = [copy["title"]]
        else:
            catalog_title_lines = _wrap_text(copy["title"], 12 if mixed_title else 8 if re.search(r"[\u4e00-\u9fff]", copy["title"]) else 16)
        catalog_subtitle_lines = subtitle_lines[:2]
        title_bump = 4 if section_role == "chapter" else 2 if section_role == "summary" else 0
        catalog_title_size = (max(34, int(width*0.050)) if len(catalog_title_lines) == 1 else max(30, int(width*0.046))) + title_bump
        catalog_title_y = height * (0.15 if section_role == "chapter" else 0.16)
        catalog_subtitle_y = catalog_title_y + len(catalog_title_lines) * catalog_title_size * 1.02 + (height * 0.022 if series_unified else height * 0.02)
        catalog_badge_y = catalog_subtitle_y + max(1, len(catalog_subtitle_lines)) * max(15, int(width*0.019)) * 1.08 + (height * 0.03 if section_role == "chapter" else height * 0.025)
        rows = bullets[:6] or ["Cursor / AI IDE / Agent 与代码库上下文", "Windsurf / Agent IDE / 流程驱动与协作", "GitHub Copilot / 编程助手 / 生态广上手快"]
        min_row_h = height * (0.105 if controls["density"] == "compact" else 0.125 if controls["density"] == "comfy" else 0.11)
        row_h, row_gap = _tight_row_metrics(height, catalog_badge_y + height * 0.042, min_row_h, len(rows))
        cards: list[str] = []
        start_y = catalog_badge_y + height * 0.03
        colors = [accent, "#F06AB2", "#35C5F2", "#43E39B", "#FFB84D", "#8B4DB4"]
        for idx, row in enumerate(rows):
            y = start_y + idx * (row_h + row_gap)
            name, role, desc = _split_catalog_row(row)
            card_body_h = row_h * 0.78
            icon_cx = width * 0.12
            title_x = width * 0.17
            name_lines, name_size = _fit_body_block(
                name,
                max_width_px=width * 0.58,
                chinese_wraps=[18, 16, 14],
                latin_wraps=[26, 22, 20],
                size_candidates=[max(26, int(width*0.032)), max(22, int(width*0.028)), max(20, int(width*0.026))],
                max_lines=2,
            )
            role_lines, role_size = _fit_body_block(
                role,
                max_width_px=width * 0.16,
                chinese_wraps=[20, 18, 16],
                latin_wraps=[28, 24, 22],
                size_candidates=[max(18, int(width*0.022)), max(16, int(width*0.020)), max(15, int(width*0.018))],
                max_lines=1,
            )
            desc_lines, desc_size = _fit_body_block(
                desc,
                max_width_px=width * 0.68,
                chinese_wraps=[34, 30, 26],
                latin_wraps=[48, 42, 36],
                size_candidates=[
                    max(18 if controls["density"] != "compact" else 17, int(width*0.022)),
                    max(16, int(width*0.020)),
                    max(15, int(width*0.018)),
                ],
                max_lines=2,
            )
            name_h = _text_block_height(name_lines, name_size, 1.02)
            desc_h = _text_block_height(desc_lines, desc_size, 1.05)
            inner_top = y + card_body_h * 0.16
            desc_gap = max(height * 0.016, card_body_h * 0.18)
            title_y = inner_top
            role_pill_y = y + card_body_h * 0.18
            desc_y = title_y + name_h + desc_gap
            max_desc_y = y + card_body_h - max(height * 0.03, card_body_h * 0.14)
            if desc_y > max_desc_y:
                desc_y = max_desc_y
            cards.append(f'<rect x="{width*0.07:.2f}" y="{y:.2f}" width="{width*0.86:.2f}" height="{card_body_h:.2f}" rx="20" fill="{"#161D2A" if theme_dark else "#FFFFFF"}"/>')
            cards.append(f'<circle cx="{icon_cx:.2f}" cy="{y + card_body_h*0.28:.2f}" r="{width*0.022:.2f}" fill="{colors[idx % len(colors)]}"/>')
            cards.append(_svg_text_block(title_x, title_y, name_lines, name_size, "#EFF3FF" if theme_dark else "#2A2F45", weight=900, line_gap=1.02))
            cards.append(f'<rect x="{width*0.72:.2f}" y="{role_pill_y:.2f}" width="{width*0.14:.2f}" height="{height*0.028:.2f}" rx="{height*0.014:.2f}" fill="{"#1A2234" if theme_dark else "#EEF2FF"}"/>')
            cards.append(_svg_text_block(width*0.79, role_pill_y + height*0.020, role_lines, role_size, accent if not theme_dark else "#BFD0FF", weight=800, anchor="middle", line_gap=1.03))
            cards.append(_svg_text_block(title_x, desc_y, desc_lines, desc_size, "#A6B0C5" if theme_dark else "#667089", weight=700, line_gap=1.05))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0F1320" if theme_dark else "#F5F6FC"}"/>
  {sparkles}
  {f'<rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.26:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="{"#1A2234" if theme_dark else "#EEF2FF"}"/>{_svg_text_block(width*0.10, height*0.105, [kicker_text], max(14, int(width*0.017)), accent if not theme_dark else "#BFD0FF", weight=800)}' if kicker_text else ''}
  {_svg_text_block(width*0.07, catalog_title_y, catalog_title_lines, catalog_title_size, "#F4F7FF" if theme_dark else "#243047", weight=900, line_gap=1.02)}
  {_title_emoji_svg(width*0.07, catalog_title_y, catalog_title_lines, catalog_title_size, trailing_title_emoji, width, accent if not theme_dark else "#BFD0FF", scale=1.7)}
  {_svg_text_block(width*0.07, catalog_subtitle_y, catalog_subtitle_lines, max(15, int(width*0.019)), "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.08)}
  {f'<rect x="{width*0.07:.2f}" y="{catalog_badge_y:.2f}" width="{width*0.16:.2f}" height="{height*0.042:.2f}" rx="18" fill="{"#1C2538" if theme_dark else "#F2EEFF"}"/>{_svg_text_block(width*0.10, catalog_badge_y + height*0.028, [copy["emphasis"]], max(18, int(width*0.022)), accent if not theme_dark else "#D3BEFF", weight=900)}' if copy["emphasis"] else ''}
  <g>{''.join(cards)}</g>
  {_svg_text_block(width*0.50, height*0.95, footer_lines, max(14, int(width*0.018)), "#8F99AF" if theme_dark else "#A7ADBF", weight=600, anchor="middle") if footer_lines else ''}
</svg>'''

    if kind == "qa":
        theme_dark = controls["theme"] == "dark"
        accent = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
        section_role = controls.get("section_role", "auto")
        kicker_text = _visible_kicker(copy)
        footer_lines = _footer_lines(copy)
        sparkles = _decor_sparkles(width, height, controls, accent, theme_dark)
        tone, _, emoji_policy = _resolved_playful_controls(controls)
        qa_items = bullets[:4] or ["问题定义：先说结论，再拆原因", "核心机制：把复杂概念拆成 3 个点", "关键数据：用数字做视觉锚点", "落地建议：最后给出行动结论"]
        cards: list[str] = []
        qa_start_y = height * (0.29 if section_role == "summary" else 0.27)
        qa_gap = height * 0.035
        qa_card_h = (height - qa_start_y - height * 0.12 - qa_gap * (len(qa_items) - 1)) / max(1, len(qa_items))
        for idx, item in enumerate(qa_items):
            y = qa_start_y + idx * (qa_card_h + qa_gap)
            q, a = _split_qa_item(item)
            q_lines, q_size = _fit_body_block(
                q,
                max_width_px=width * 0.60,
                chinese_wraps=[18, 16, 14],
                latin_wraps=[28, 24, 20],
                size_candidates=[
                    max(24 if controls["density"] != "compact" else 22, int(width*0.030)),
                    max(20, int(width*0.026)),
                    max(18, int(width*0.024)),
                ],
                max_lines=2,
            )
            a_lines, a_size = ([], 0)
            if a:
                a_lines, a_size = _fit_body_block(
                    a,
                    max_width_px=width * 0.62,
                    chinese_wraps=[28, 24, 22],
                    latin_wraps=[42, 36, 32],
                    size_candidates=[
                        max(19 if controls["density"] == "comfy" else 18, int(width*0.023)),
                        max(16, int(width*0.020)),
                        max(15, int(width*0.018)),
                    ],
                    max_lines=2,
                )
            cards.append(f'<rect x="{width*0.08:.2f}" y="{y:.2f}" width="{width*0.84:.2f}" height="{qa_card_h:.2f}" rx="22" fill="{"#161D2A" if theme_dark else "#FFFFFF"}"/>')
            cards.append(f'<rect x="{width*0.10:.2f}" y="{y + qa_card_h*0.18:.2f}" width="{width*0.010:.2f}" height="{qa_card_h*0.48:.2f}" rx="8" fill="{accent if not theme_dark else "#2C4F7A"}"/>')
            cards.append(f'<rect x="{width*0.77:.2f}" y="{y + qa_card_h*0.16:.2f}" width="{width*0.09:.2f}" height="{height*0.028:.2f}" rx="{height*0.014:.2f}" fill="{"#1A2234" if theme_dark else "#EEF2FF"}"/>')
            label = f"Q{idx + 1}" if tone != "playful" or emoji_policy == "none" else ["❓", "💡", "🧠", "✅"][idx % 4]
            cards.append(_svg_text_block(width*0.815, y + qa_card_h*0.16 + height*0.020, [label], max(14, int(width*0.017)), accent if not theme_dark else "#BFD0FF", weight=900, anchor="middle"))
            cards.append(_svg_text_block(width*0.16, y + qa_card_h*0.34, q_lines, q_size, "#F1F5FF" if theme_dark else "#22263A", weight=900, line_gap=1.05))
            if a_lines:
                cards.append(_svg_text_block(width*0.16, y + qa_card_h*0.66, a_lines, a_size, "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.1))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0F1320" if theme_dark else "#F5F6FC"}"/>
  {sparkles}
  {f'<rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.24:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="{"#1A2234" if theme_dark else "#EEF2FF"}"/>{_svg_text_block(width*0.10, height*0.105, [kicker_text], max(14, int(width*0.017)), accent if not theme_dark else "#BFD0FF", weight=800)}' if kicker_text else ''}
  {_svg_text_block(width*0.08, height*0.17, title_lines, max(38, int(width*0.056)), "#F4F7FF" if theme_dark else "#243047", weight=900, line_gap=1.06)}
  {_title_emoji_svg(width*0.08, height*0.17, title_lines, max(38, int(width*0.056)), trailing_title_emoji, width, accent if not theme_dark else "#BFD0FF", scale=1.75)}
  {_svg_text_block(width*0.08, height*0.24, subtitle_lines[:2], max(18, int(width*0.022)), "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.08)}
  <g>{''.join(cards)}</g>
  {_svg_text_block(width*0.50, height*0.94, footer_lines, max(14, int(width*0.018)), "#8F99AF" if theme_dark else "#A7ADBF", weight=600, anchor="middle") if footer_lines else ''}
</svg>'''

    if kind == "timeline":
        theme_dark = controls["theme"] == "dark"
        accent = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
        series_unified = controls.get("series_style") == "unified"
        section_role = controls.get("section_role", "auto")
        kicker_text = _visible_kicker(copy)
        points = bullets[:5] or ["提出概念", "官方定名", "行业采用", "规模增长", "共识形成"]
        if not _timeline_supports_text(points):
            kind = "mechanism"
        else:
            nodes: list[str] = []
            timeline_title_size = max(38, int(width*0.056)) + (4 if section_role == "chapter" else 2 if section_role == "summary" else 0)
            title_y = height * (0.16 if section_role == "chapter" else 0.18)
            subtitle_y = title_y + _text_block_height(title_lines, timeline_title_size, 1.06) + (height * 0.03 if section_role == "chapter" else height * 0.026)
            base_y = subtitle_y + _text_block_height(subtitle_lines[:2], max(18, int(width*0.022)), 1.08) + (height * 0.10 if series_unified else height * 0.08)
            spacing = width * 0.18
            start_x = width * 0.14
            nodes.append(f'<path d="M {start_x:.2f} {base_y:.2f} L {start_x + spacing*(len(points)-1):.2f} {base_y:.2f}" stroke="{"#34415A" if theme_dark else "#C9D0EA"}" stroke-width="4" stroke-linecap="round"/>')
            colors = [accent, "#F06AB2", "#35C5F2", "#43E39B", "#FFB84D"]
            for idx, item in enumerate(points):
                x = start_x + spacing * idx
                point_lines, point_size = _fit_body_block(
                    item,
                    max_width_px=width * 0.18,
                    chinese_wraps=[10, 8, 7],
                    latin_wraps=[14, 12, 10],
                    size_candidates=[
                        max(19 if controls["density"] == "comfy" else 18, int(width*0.023)),
                        max(16, int(width*0.020)),
                        max(14, int(width*0.018)),
                    ],
                    max_lines=2,
                )
                nodes.append(f'<circle cx="{x:.2f}" cy="{base_y:.2f}" r="{width*0.028:.2f}" fill="{colors[idx % len(colors)]}"/>')
                nodes.append(_svg_text_block(x, base_y + height*0.11, point_lines, point_size, "#E8EEFF" if theme_dark else "#394156", weight=800, anchor="middle", line_gap=1.08))
            return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0F1320" if theme_dark else "#F5F6FC"}"/>
  {f'<rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.20:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="{"#1A2234" if theme_dark else "#EEF2FF"}"/>{_svg_text_block(width*0.10, height*0.105, [kicker_text], max(14, int(width*0.017)), accent if not theme_dark else "#BFD0FF", weight=800)}' if kicker_text else ''}
  {_svg_text_block(width*0.08, title_y, title_lines, timeline_title_size, "#F4F7FF" if theme_dark else "#243047", weight=900, line_gap=1.06)}
  {_svg_text_block(width*0.08, subtitle_y, subtitle_lines[:2], max(18, int(width*0.022)), "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.08)}
  <g>{''.join(nodes)}</g>
  {f'<rect x="{width*0.08:.2f}" y="{height*0.68:.2f}" width="{width*0.84:.2f}" height="{height*0.14:.2f}" rx="24" fill="{"#171F2D" if theme_dark else "#FFFFFF"}"/>{_svg_text_block(width*0.12, height*0.73, _wrap_text(copy["emphasis"], 12), max(24, int(width*0.032)), accent if not theme_dark else "#D3BEFF", weight=900)}{_svg_text_block(width*0.28, height*0.73, subtitle_lines[:2], max(18, int(width*0.022)), "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.08)}' if copy["emphasis"] else ''}
</svg>'''

    if kind == "comparison":
        theme_dark = controls["theme"] == "dark"
        accent = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
        series_unified = controls.get("series_style") == "unified"
        section_role = controls.get("section_role", "auto")
        kicker_text = _visible_kicker(copy)
        footer_lines = _footer_lines(copy)
        rows = bullets[:5] or ["以前：手动整理", "现在：自动筛选", "以前：逐条处理", "现在：结果直达"]
        comparison_title_lines = title_lines
        comparison_title_size = title_size + (4 if section_role == "chapter" else 2 if section_role == "summary" else 0)
        title_y = height * (0.155 if section_role == "chapter" else 0.17)
        subtitle_y = title_y + _text_block_height(comparison_title_lines, comparison_title_size, 1.04) + (height * 0.024 if series_unified else height * 0.02)
        header_bar_y = subtitle_y + _text_block_height(subtitle_lines[:2], subtitle_size, 1.08) + (height * 0.034 if section_role == "chapter" else height * 0.03)
        min_row_h = height * (0.10 if controls["density"] == "compact" else 0.12 if controls["density"] == "comfy" else 0.11)
        row_h, row_gap = _tight_row_metrics(height, header_bar_y + height * 0.07, min_row_h, len(rows))
        body: list[str] = []
        start_y = header_bar_y + height * 0.08
        for idx, row in enumerate(rows):
            y = start_y + idx * (row_h + row_gap)
            scene, before, after = _split_comparison_row(row)
            scene_lines, scene_size = _fit_body_block(
                scene,
                max_width_px=width * 0.24,
                chinese_wraps=[18, 16, 14],
                latin_wraps=[22, 20, 18],
                size_candidates=[
                    max(27 if controls["density"] != "compact" else 26, int(width*0.032)),
                    max(24, int(width*0.028)),
                    max(22, int(width*0.026)),
                ],
                max_lines=2,
            )
            before_lines, before_size = _fit_body_block(
                before,
                max_width_px=width * 0.24,
                chinese_wraps=[20, 18, 16],
                latin_wraps=[26, 24, 22],
                size_candidates=[
                    max(25 if controls["density"] == "comfy" else 24, int(width*0.028)),
                    max(22, int(width*0.025)),
                    max(20, int(width*0.023)),
                ],
                max_lines=2,
            )
            after_lines, after_size = _fit_body_block(
                after,
                max_width_px=width * 0.24,
                chinese_wraps=[20, 18, 16],
                latin_wraps=[26, 24, 22],
                size_candidates=[
                    max(25 if controls["density"] == "comfy" else 24, int(width*0.028)),
                    max(22, int(width*0.025)),
                    max(20, int(width*0.023)),
                ],
                max_lines=2,
            )
            body.append(f'<rect x="{width*0.07:.2f}" y="{y:.2f}" width="{width*0.86:.2f}" height="{row_h*0.86:.2f}" rx="18" fill="{"#171F2D" if theme_dark else "#FFFFFF"}" fill-opacity="0.92"/>')
            body.append(_svg_text_block(width*0.10, y + row_h*0.30, scene_lines, scene_size, "#EFF3FF" if theme_dark else "#2A2F45", weight=800, line_gap=1.08))
            body.append(_svg_text_block(width*0.34, y + row_h*0.25, before_lines, before_size, "#A6B0C5" if theme_dark else "#41485F", weight=700, line_gap=1.08))
            body.append(_svg_text_block(width*0.62, y + row_h*0.25, after_lines, after_size, accent if not theme_dark else "#BFD0FF", weight=800, line_gap=1.08))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0F1320" if theme_dark else "#F5F6FC"}"/>
  <rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.86:.2f}" height="{height*0.035:.2f}" rx="{height*0.017:.2f}" fill="url(#bar)"/>
  <defs>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{accent}"/>
      <stop offset="100%" stop-color="{"#8B4DB4" if accent != "#D96DB4" else "#5B82F4"}"/>
    </linearGradient>
  </defs>
  {_svg_text_block(width*0.09, height*0.105, [kicker_text], max(14, int(width*0.017)), "#FFFFFF", weight=800) if kicker_text else ''}
  {_svg_text_block(width*0.07, title_y, comparison_title_lines, comparison_title_size, accent if not theme_dark else "#BFD0FF", weight=900, line_gap=1.04)}
  {_svg_text_block(width*0.07, subtitle_y, subtitle_lines[:2], subtitle_size, "#A6B0C5" if theme_dark else "#7E869B", weight=700, line_gap=1.08)}
  <rect x="{width*0.07:.2f}" y="{header_bar_y:.2f}" width="{width*0.86:.2f}" height="{height*0.055:.2f}" rx="18" fill="{"#25314A" if theme_dark else "#7C63D8"}"/>
  {_svg_text_block(width*0.10, header_bar_y + height*0.036, ["场景"], max(19, int(width*0.023)), "#FFFFFF", weight=800)}
  {_svg_text_block(width*0.34, header_bar_y + height*0.036, ["以前"], max(19, int(width*0.023)), "#FFFFFF", weight=800)}
  {_svg_text_block(width*0.62, header_bar_y + height*0.036, ["现在"], max(19, int(width*0.023)), "#FFFFFF", weight=800)}
  <g>{''.join(body)}</g>
  {_svg_text_block(width*0.50, height*0.94, footer_lines, max(14, int(width*0.018)), "#8F99AF" if theme_dark else "#9AA0B5", weight=600, anchor="middle") if footer_lines else ''}
</svg>'''

    if kind == "flow":
        theme_dark = controls["theme"] == "dark"
        accent = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
        series_unified = controls.get("series_style") == "unified"
        section_role = controls.get("section_role", "auto")
        kicker_text = _visible_kicker(copy)
        footer_lines = _footer_lines(copy)
        steps = bullets[:5] or ["写完文章", "Agent 唤醒", "自动翻译", "推送发布", "状态更新"]
        nodes: list[str] = []
        arrows: list[str] = []
        circle_colors = [accent, "#F06AB2", "#35C5F2", "#43E39B", "#FFB84D"]
        flow_specs: list[tuple[list[str], int, list[str], int, float]] = []
        min_step_h = height * (0.105 if controls["density"] == "compact" else 0.118 if controls["density"] == "comfy" else 0.11)
        flow_title_size = max(38, int(width*0.056)) + (4 if section_role == "chapter" else 2 if section_role == "summary" else 0)
        title_y = height * (0.09 if section_role == "chapter" else 0.10)
        subtitle_y = title_y + _text_block_height([copy["title"]], flow_title_size, 1.0) + (height * 0.028 if section_role == "chapter" else height * 0.022)
        content_top = subtitle_y + _text_block_height(subtitle_lines, max(18, int(width*0.022)), 1.08) + (height * 0.045 if series_unified else height * 0.04)
        available_h = height - content_top - height * 0.12
        for step in steps:
            title, desc = _split_bullet_copy(step)
            flow_title_lines, flow_title_size = _fit_body_block(
                title,
                max_width_px=width * 0.57,
                chinese_wraps=[20, 18, 16],
                latin_wraps=[32, 28, 24],
                size_candidates=[
                    max(24 if controls["density"] != "compact" else 22, int(width*0.032)),
                    max(20, int(width*0.027)),
                    max(18, int(width*0.024)),
                ],
                max_lines=2,
            )
            flow_desc_lines, flow_desc_size = _fit_body_block(
                desc,
                max_width_px=width * 0.57,
                chinese_wraps=[28, 24, 22],
                latin_wraps=[42, 36, 32],
                size_candidates=[
                    max(19 if controls["density"] == "comfy" else 18, int(width*0.023)),
                    max(16, int(width*0.020)),
                    max(15, int(width*0.018)),
                ],
                max_lines=2,
            )
            title_h = _text_block_height(flow_title_lines, flow_title_size, 1.06)
            desc_h = _text_block_height(flow_desc_lines, flow_desc_size, 1.10)
            card_h = max(min_step_h * 0.72, height * 0.036 + title_h + desc_h + height * 0.040)
            flow_specs.append((flow_title_lines, flow_title_size, flow_desc_lines, flow_desc_size, card_h))
        total_cards_h = sum(spec[4] for spec in flow_specs)
        arrow_gap = height * 0.028
        total_needed = total_cards_h + arrow_gap * max(0, len(flow_specs) - 1)
        if total_needed > available_h and total_needed > 0:
            scale = available_h / total_needed
            resized_specs: list[tuple[list[str], int, list[str], int, float]] = []
            for flow_title_lines, flow_title_size, flow_desc_lines, flow_desc_size, card_h in flow_specs:
                resized_specs.append((flow_title_lines, flow_title_size, flow_desc_lines, flow_desc_size, card_h * scale))
            flow_specs = resized_specs
            arrow_gap *= scale
        current_y = content_top
        for idx, (flow_title_lines, flow_title_size, flow_desc_lines, flow_desc_size, card_h) in enumerate(flow_specs):
            y = current_y
            current_y += card_h + arrow_gap
            nodes.append(f'<rect x="{width*0.12:.2f}" y="{y:.2f}" width="{width*0.78:.2f}" height="{card_h:.2f}" rx="22" fill="{"#161D2A" if theme_dark else "#FFFFFF"}"/>')
            nodes.append(f'<circle cx="{width*0.17:.2f}" cy="{y + card_h*0.36:.2f}" r="{width*0.038:.2f}" fill="{circle_colors[idx % len(circle_colors)]}"/>')
            nodes.append(_svg_text_block(width*0.17, y + card_h*0.39, [str(idx + 1)], max(18, int(width*0.022)), "#FFFFFF", weight=900, anchor="middle"))
            card_title_y = y + max(height * 0.022, card_h * 0.18)
            desc_y = card_title_y + _text_block_height(flow_title_lines, flow_title_size, 1.06) + max(height * 0.012, card_h * 0.10)
            nodes.append(_svg_text_block(width*0.25, card_title_y, flow_title_lines, flow_title_size, "#F1F5FF" if theme_dark else "#22263A", weight=800, line_gap=1.06))
            nodes.append(_svg_text_block(width*0.25, desc_y, flow_desc_lines, flow_desc_size, "#A6B0C5" if theme_dark else "#8A90A8", weight=700, line_gap=1.1))
            if idx < len(flow_specs) - 1:
                arrow_top = y + card_h
                arrow_bottom = arrow_top + arrow_gap * 0.72
                arrows.append(f'<path d="M {width*0.50:.2f} {arrow_top:.2f} L {width*0.50:.2f} {arrow_bottom:.2f}" stroke="{"#3A465E" if theme_dark else "#CBD2EA"}" stroke-width="3" stroke-linecap="round"/>')
                arrows.append(_svg_text_block(width*0.50, arrow_bottom + height*0.008, ["↓"], max(18, int(width*0.024)), "#8F99AF" if theme_dark else "#B9BED2", weight=700, anchor="middle"))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0F1320" if theme_dark else "#F5F6FC"}"/>
  {f'<rect x="{width*0.07:.2f}" y="{height*0.075:.2f}" width="{width*0.54:.2f}" height="{height*0.04:.2f}" rx="{height*0.02:.2f}" fill="{"#1A2234" if theme_dark else "#E6EBFF"}"/>{_svg_text_block(width*0.10, height*0.103, [kicker_text], max(14, int(width*0.017)), accent if not theme_dark else "#BFD0FF", weight=800)}' if kicker_text else ''}
  {_svg_text_block(width*0.07, title_y, [copy["title"]], flow_title_size, "#F4F7FF" if theme_dark else "#29304C", weight=900)}
  {_svg_text_block(width*0.07, subtitle_y, subtitle_lines, max(18, int(width*0.022)), "#A6B0C5" if theme_dark else "#8A90A8", weight=700, line_gap=1.08)}
  <g>{''.join(nodes)}</g>
  <g>{''.join(arrows)}</g>
  {_svg_text_block(width*0.50, height*0.95, footer_lines, max(14, int(width*0.018)), "#8F99AF" if theme_dark else "#A7ADBF", weight=600, anchor="middle") if footer_lines else ''}
</svg>'''

    cards: list[str] = []
    theme_dark = controls["theme"] == "dark"
    accent = "#5B82F4" if controls["accent"] in {"auto", "blue"} else "#45B97C" if controls["accent"] == "green" else "#E67E22" if controls["accent"] == "warm" else "#D96DB4"
    series_unified = controls.get("series_style") == "unified"
    section_role = controls.get("section_role", "auto")
    sparkles = _decor_sparkles(width, height, controls, accent, theme_dark)
    tone, _, emoji_policy = _resolved_playful_controls(controls)
    mechanism_items = bullets[:4] or ["读到结构快照", "页面可持续读取", "同一任务链保留上下文", "关键信息分层呈现"]
    mechanism_subtitle_lines = subtitle_lines[:2]
    title_y = height * (0.155 if section_role == "chapter" else 0.17)
    subtitle_y = title_y + _text_block_height(title_lines, title_size, 1.08) + (height * 0.024 if series_unified else height * 0.02)
    badge_y = subtitle_y + _text_block_height(mechanism_subtitle_lines, subtitle_size, 1.08) + (height * 0.034 if section_role == "chapter" else height * 0.028)
    kicker_text = _visible_kicker(copy)
    if kicker_text:
        title_y = max(title_y, height * 0.20)
        subtitle_y = title_y + _text_block_height(title_lines, title_size, 1.08) + (height * 0.024 if series_unified else height * 0.02)
        badge_y = subtitle_y + _text_block_height(mechanism_subtitle_lines, subtitle_size, 1.08) + (height * 0.034 if section_role == "chapter" else height * 0.028)
    footer_lines = _footer_lines(copy)
    footer_size = max(15, int(width * 0.02))
    footer_h = _text_block_height(footer_lines, footer_size, 1.08)
    footer_reserved = max(height * 0.05, footer_h + height * 0.08) if footer_lines else height * 0.05
    card_h, card_gap = _tight_row_metrics(height, badge_y + height * 0.054, footer_reserved, len(mechanism_items))
    cards_start_y = badge_y + height * 0.068
    last_card_bottom = cards_start_y + len(mechanism_items) * card_h + max(0, len(mechanism_items) - 1) * card_gap
    footer_y = min(height * 0.93, last_card_bottom + height * 0.05)
    colors = [accent, "#E284F1" if not theme_dark else "#D96DB4", "#4AA6F0" if not theme_dark else "#7AA2FF", "#45B97C" if not theme_dark else "#66D39E"]
    for idx, item in enumerate(mechanism_items):
        y = cards_start_y + idx * (card_h + card_gap)
        item_lines, item_size = _fit_body_block(
            item,
            max_width_px=width * 0.58,
            chinese_wraps=[28, 24, 22],
            latin_wraps=[40, 36, 32],
            size_candidates=[max(24, int(width*0.030)), max(22, int(width*0.028)), max(20, int(width*0.026))],
            max_lines=2,
        )
        cards.append(f'<rect x="{width*0.08:.2f}" y="{y:.2f}" width="{width*0.84:.2f}" height="{card_h:.2f}" rx="20" fill="{"#161C29" if theme_dark else "#FFFFFF"}"/>')
        cards.append(f'<rect x="{width*0.10:.2f}" y="{y + card_h*0.18:.2f}" width="{width*0.010:.2f}" height="{card_h*0.56:.2f}" rx="6" fill="{colors[idx % len(colors)]}"/>')
        cards.append(f'<rect x="{width*0.76:.2f}" y="{y + card_h*0.16:.2f}" width="{width*0.10:.2f}" height="{height*0.028:.2f}" rx="{height*0.014:.2f}" fill="{"#273147" if theme_dark else "#EEF2FF"}"/>')
        label = f"要点{idx + 1}" if tone != "playful" or emoji_policy == "none" else ["🧩", "⚙️", "📌", "✨"][idx % 4]
        cards.append(_svg_text_block(width*0.81, y + card_h*0.16 + height*0.020, [label], max(14, int(width*0.017)), accent if theme_dark else "#6A73D8", weight=800, anchor="middle"))
        cards.append(_svg_text_block(width*0.16, y + card_h*0.40, item_lines, item_size, "#EEF3FF" if theme_dark else "#394156", weight=800, line_gap=1.08))
        if idx < len(mechanism_items) - 1:
            cards.append(f'<path d="M {width*0.10:.2f} {y + card_h + card_gap*0.38:.2f} L {width*0.92:.2f} {y + card_h + card_gap*0.38:.2f}" stroke="{"#232D40" if theme_dark else "#EEF1F6"}" stroke-width="2"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{"#0E1320" if theme_dark else "#F5F6FC"}"/>
  {sparkles}
  {_svg_text_block(width*0.08, height*0.11, [kicker_text], max(15, int(width*0.018)), accent if theme_dark else "#6B74D8", weight=800) if kicker_text else ''}
  {_svg_text_block(width*0.08, title_y, title_lines, title_size, "#F2F6FF" if theme_dark else "#253044", weight=900, line_gap=1.08)}
  {_title_emoji_svg(width*0.08, title_y, title_lines, title_size, trailing_title_emoji if len(''.join(title_lines)) <= 14 else "", width, accent if not theme_dark else "#BFD0FF", scale=1.55)}
  {_svg_text_block(width*0.08, subtitle_y, mechanism_subtitle_lines, subtitle_size, "#B7C0D5" if theme_dark else "#7E869B", weight=700, line_gap=1.08)}
  {f'<rect x="{width*0.08:.2f}" y="{badge_y:.2f}" width="{width*0.22:.2f}" height="{height*0.042:.2f}" rx="{height*0.02:.2f}" fill="{"#2B2540" if theme_dark else "#F2EEFF"}"/>{_svg_text_block(width*0.11, badge_y + height*0.028, [copy["emphasis"]], max(18, int(width*0.022)), accent if theme_dark else "#7A59E6", weight=900)}' if copy["emphasis"] else ''}
  <g>{''.join(cards)}</g>
  {_svg_text_block(width*0.50, footer_y, footer_lines, footer_size, "#9EABC3" if theme_dark else "#7E869B", weight=700, anchor="middle") if footer_lines else ''}
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
    if _is_infographic_prompt(prompt):
        return _compose_infographic_svg(prompt, width, height)
    if _is_text_cover_prompt(prompt):
        return _compose_text_cover_svg(prompt, width, height)
    if _is_cover_prompt(prompt):
        return _compose_cover_svg(prompt, width, height)
    return _compose_illustration_svg(prompt, width, height)


def _append_render_controls(
    prompt: str,
    theme: str,
    density: str,
    surface_style: str,
    accent: str,
    series_style: str = "auto",
    section_role: str = "auto",
    tone: str = "auto",
    decor_level: str = "auto",
    emoji_policy: str = "auto",
    emoji_render_mode: str = "auto",
    cover_layout: str = "auto",
    hero_emoji: str = "",
) -> str:
    parts = [prompt]
    if theme and theme != "auto":
        parts.append(f"主题：{theme}")
    if density and density != "auto":
        parts.append(f"页面密度：{density}")
    if series_style and series_style != "auto":
        parts.append(f"系列风格：{series_style}")
    if section_role and section_role != "auto":
        parts.append(f"页面角色：{section_role}")
    if surface_style and surface_style != "auto":
        parts.append(f"页面风格：{surface_style}")
    if accent and accent != "auto":
        parts.append(f"强调色：{accent}")
    if tone and tone != "auto":
        parts.append(f"语气：{tone}")
    if decor_level and decor_level != "auto":
        parts.append(f"装饰密度：{decor_level}")
    if emoji_policy and emoji_policy != "auto":
        parts.append(f"表情策略：{emoji_policy}")
    if emoji_render_mode and emoji_render_mode != "auto":
        parts.append(f"表情渲染：{emoji_render_mode}")
    if cover_layout and cover_layout != "auto":
        parts.append(f"封面布局：{cover_layout}")
    if hero_emoji:
        parts.append(f"主视觉表情：{hero_emoji}")
    return "\n".join(parts)


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
    if shutil.which("sips"):
        if run(["sips", "-s", "format", "png", str(svg_path), "--out", str(png_path)]):
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
            if ql_ok and preview_path.exists():
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
    if shutil.which("magick"):
        if run(["magick", "-background", "none", str(svg_path), str(png_path)]):
            return

    if EXPORT_FALLBACK_SCRIPT.exists() and run(["bash", str(EXPORT_FALLBACK_SCRIPT), str(svg_path), str(png_path), str(width), str(height)]):
        return

    raise RuntimeError("No local SVG renderer found. Install rsvg-convert, inkscape, ImageMagick, or ensure macOS sips supports SVG.")


def _normalize_svg_markup(svg_markup: str, width: int, height: int) -> str:
    markup = svg_markup.strip()
    if not markup.startswith("<svg"):
        raise ValueError("custom SVG must start with <svg")

    match = re.match(r"<svg\b([^>]*)>", markup, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError("custom SVG is missing a valid opening <svg> tag")

    attrs = match.group(1)

    def _set_attr(blob: str, name: str, value: str) -> str:
        pattern = rf'(\s{name}\s*=\s*")[^"]*(")'
        if re.search(pattern, blob):
            return re.sub(pattern, lambda m: f'{m.group(1)}{value}{m.group(2)}', blob)
        return f'{blob} {name}="{value}"'

    attrs = _set_attr(attrs, "xmlns", "http://www.w3.org/2000/svg")
    attrs = _set_attr(attrs, "width", str(width))
    attrs = _set_attr(attrs, "height", str(height))
    attrs = _set_attr(attrs, "viewBox", f"0 0 {width} {height}")
    return f"<svg{attrs}>" + markup[match.end():]


def generate_image_from_svg_markup(
    svg_markup: str,
    output: str | Path,
    width: int,
    height: int,
    svg_output: str | Path | None = None,
    keep_svg: bool = False,
) -> dict[str, Any]:
    png_path = Path(output).expanduser().resolve()
    normalized_svg = _normalize_svg_markup(svg_markup, width, height)
    if svg_output:
        svg_path = Path(svg_output).expanduser().resolve()
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(normalized_svg, encoding="utf-8")
        export_svg_to_png(svg_path, png_path, width, height)
    elif keep_svg:
        svg_path = png_path.with_suffix(".svg")
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(normalized_svg, encoding="utf-8")
        export_svg_to_png(svg_path, png_path, width, height)
    else:
        png_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="free-imagegen-svg-") as tmpdir:
            svg_path = Path(tmpdir) / f"{png_path.stem}.svg"
            svg_path.write_text(normalized_svg, encoding="utf-8")
            export_svg_to_png(svg_path, png_path, width, height)
    return {
        "mode": "direct-svg-to-png",
        "svg": str(svg_path) if (svg_output or keep_svg) else None,
        "png": str(png_path),
        "width": width,
        "height": height,
        "composition": "custom_svg",
    }


def generate_image(
    prompt: str,
    output: str | Path,
    width: int,
    height: int,
    svg_output: str | Path | None = None,
    keep_svg: bool = False,
) -> dict[str, Any]:
    png_path = Path(output).expanduser().resolve()
    svg_content = _compose_svg(prompt, width, height)
    if svg_output:
        svg_path = Path(svg_output).expanduser().resolve()
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(svg_content, encoding="utf-8")
        export_svg_to_png(svg_path, png_path, width, height)
    elif keep_svg:
        svg_path = png_path.with_suffix(".svg")
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(svg_content, encoding="utf-8")
        export_svg_to_png(svg_path, png_path, width, height)
    else:
        png_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="free-imagegen-svg-") as tmpdir:
            svg_path = Path(tmpdir) / f"{png_path.stem}.svg"
            svg_path.write_text(svg_content, encoding="utf-8")
            export_svg_to_png(svg_path, png_path, width, height)

    return {
        "mode": "local-svg-to-png",
        "prompt": prompt,
        "svg": str(svg_path) if (svg_output or keep_svg) else None,
        "png": str(png_path),
        "width": width,
        "height": height,
        "composition": (
            "infographic"
            if _is_infographic_prompt(prompt)
            else "text_cover"
            if _is_text_cover_prompt(prompt)
            else "cover"
            if _is_cover_prompt(prompt)
            else "illustration"
        ),
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


def generate_openclaw_assets(project_dir: str | Path, prompt: str, keep_svg: bool = False) -> dict[str, Any]:
    project = Path(project_dir).expanduser().resolve()
    if not project.exists():
        raise FileNotFoundError(f"Project directory not found: {project}")

    assets = project / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    thumbnail_png = assets / "thumbnail.png"
    icon_png = assets / "icon.png"
    thumbnail_svg = assets / "thumbnail.svg" if keep_svg else None
    icon_svg = assets / "icon.svg" if keep_svg else None

    generate_image(
        prompt=f"{prompt} cover thumbnail 海报",
        output=thumbnail_png,
        width=1024,
        height=576,
        svg_output=thumbnail_svg,
        keep_svg=keep_svg,
    )
    generate_image(
        prompt=f"{prompt} icon illustration",
        output=icon_png,
        width=384,
        height=384,
        svg_output=icon_svg,
        keep_svg=keep_svg,
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
        "thumbnail_svg": str(thumbnail_svg) if thumbnail_svg else None,
        "icon_png": str(icon_png),
        "icon_svg": str(icon_svg) if icon_svg else None,
        "manifest": str(manifest_path) if manifest_path else None,
        "manifest_updated": manifest_updated,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local free text-to-image by SVG then PNG")
    parser.add_argument("--prompt", help="Text prompt")
    parser.add_argument("--prompt-file", help="Read prompt/article text from local file")
    parser.add_argument("--story-plan-file", help="Read an agent-authored story plan JSON and render pages from it")
    parser.add_argument("--output", help="Output PNG path")
    parser.add_argument("--svg-output", help="Output SVG path (optional)")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--openclaw-project", help="Generate assets/thumbnail+icon for OpenClaw project")
    parser.add_argument("--story-output-dir", help="Generate a multi-image article story set into this directory")
    parser.add_argument("--story-strategy", choices=["auto", "story", "dense", "visual"], default="auto", help="Story strategy for article-to-image sets")
    parser.add_argument("--story-image", action="append", default=[], help="Attach a real image to article story pages; repeatable")
    parser.add_argument("--keep-svg", action="store_true", help="Keep exported SVG files alongside PNG output")
    parser.add_argument("--theme", choices=["auto", "light", "dark"], default="auto", help="Overall image theme")
    parser.add_argument("--page-density", choices=["auto", "comfy", "compact"], default="auto", help="Text spacing density")
    parser.add_argument("--series-style", choices=["auto", "loose", "unified"], default="auto", help="How strongly pages in a set should feel like one series")
    parser.add_argument("--section-role", choices=["auto", "cover", "chapter", "body", "summary"], default="auto", help="Page role hint for this render")
    parser.add_argument("--surface-style", choices=["auto", "soft", "card", "minimal", "editorial"], default="auto", help="Overall surface style hint")
    parser.add_argument("--accent", choices=["auto", "blue", "green", "warm", "rose"], default="auto", help="Accent color family")
    parser.add_argument("--tone", choices=["auto", "calm", "playful", "bold", "editorial"], default="auto", help="Overall tone hint for expressive vs restrained rendering")
    parser.add_argument("--decor-level", choices=["auto", "none", "low", "medium"], default="auto", help="How much decorative treatment to allow")
    parser.add_argument("--emoji-policy", choices=["auto", "none", "sparse", "expressive"], default="auto", help="How freely emoji-style accents may appear")
    parser.add_argument("--emoji-render-mode", choices=["auto", "font", "svg", "mono", "none"], default="auto", help="How emoji-like accents should be rendered")
    parser.add_argument("--cover-layout", choices=["auto", "title_first", "hero_emoji_top"], default="auto", help="Cover composition strategy")
    parser.add_argument("--hero-emoji", default="", help="Explicit hero emoji for cover-style pages")
    parser.add_argument("--outline-only", action="store_true", help="Write analysis and outline only")
    parser.add_argument("--prompts-only", action="store_true", help="Write analysis, outline, and prompt files only")
    parser.add_argument("--images-only", action="store_true", help="Generate images using existing or regenerated prompt files")
    args = parser.parse_args(argv)
    if not args.prompt and not args.prompt_file and not args.story_plan_file:
        parser.error("one of --prompt, --prompt-file, or --story-plan-file is required")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        prompt = args.prompt
        if args.prompt_file:
            prompt = Path(args.prompt_file).expanduser().read_text(encoding="utf-8")
        story_plan = None
        if args.story_plan_file:
            story_plan = _validate_story_plan(json.loads(Path(args.story_plan_file).expanduser().read_text(encoding="utf-8")))
            if prompt is None:
                prompt = story_plan.get("title", "Agent story plan")
        if prompt is not None:
            prompt = _append_render_controls(
                prompt,
                args.theme,
                args.page_density,
                args.surface_style,
                args.accent,
                args.series_style,
                args.section_role,
                args.tone,
                args.decor_level,
                args.emoji_policy,
                args.emoji_render_mode,
                args.cover_layout,
                args.hero_emoji,
            )

        if args.openclaw_project:
            result = generate_openclaw_assets(args.openclaw_project, prompt, keep_svg=args.keep_svg)
        elif args.story_output_dir or args.story_plan_file:
            story_mode = "all"
            if args.outline_only:
                story_mode = "outline-only"
            elif args.prompts_only:
                story_mode = "prompts-only"
            elif args.images_only:
                story_mode = "images-only"
            story_output_dir = args.story_output_dir
            if not story_output_dir:
                title_source = _default_output_label(prompt, story_plan=story_plan)
                story_output_dir = str(DEFAULT_OUTPUT_DIR / _timestamp_slug("story", title_source))
            result = generate_article_story(
                prompt,
                story_output_dir,
                args.width,
                args.height,
                strategy=args.story_strategy,
                mode=story_mode,
                story_images=args.story_image,
                story_plan=story_plan,
                keep_svg=args.keep_svg,
            )
        else:
            output = args.output
            if not output:
                DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                output = str(DEFAULT_OUTPUT_DIR / f"{_timestamp_slug('image', _default_output_label(prompt))}.png")
            result = generate_image(prompt, output, args.width, args.height, args.svg_output, keep_svg=args.keep_svg)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

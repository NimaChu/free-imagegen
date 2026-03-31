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


def _normalize_dedupe_text(text: str) -> str:
    return re.sub(r'[\"“”\s，。！？!：:；;\-—·]+', "", text)


def _is_section_heading(line: str) -> bool:
    if not line:
        return False
    if len(line) <= 28 and any(token in line for token in ["为什么", "写在最后", "联系我们", "官方公告", "震撼数据", "硬伤", "更配", "配置", "步骤"]):
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


def _derive_article_copy(prompt: str, mode: str = "infographic") -> dict[str, Any]:
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

    def score_line(text: str) -> int:
        score = 0
        if len(text) < 8 or len(text) > 44:
            return -99
        if any(token in text for token in ["家人们", "炸了", "out"]):
            score -= 8
        if any(token in text for token in ["正式定名", "优先推荐", "官方", "发布试用", "明确使用", "中文名"]):
            score += 7
        if any(token in text for token in ["调用量", "增长", "关键指标", "突破", "万亿", "倍", "%"]):
            score += 6
        if any(token in text for token in ["既体现", "强调", "扩展", "原因", "本质", "语义", "多模态", "遵循"]):
            score += 5
        if any(token in text for token in ["词元", "Token", "Prompt"]):
            score += 3
        if "2026 年 3 月" in text or "3 月 25 日" in text:
            score += 1
        return score

    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for raw in candidate_lines:
        clean = re.sub(r"\s+", " ", _clean_line(raw)).strip(" ,，。；;")
        dedupe_key = _normalize_dedupe_text(clean)
        if not clean or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        ranked.append((score_line(clean), clean))

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
    emphasis = _pick_stat_phrase(prompt) or "3"
    return {
        "title": title,
        "subtitle": subtitle,
        "kicker": kicker,
        "emphasis": emphasis,
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
    pieces = ["<g>"]
    for idx, line in enumerate(lines):
        line_y = y + idx * size * line_gap
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


def _fit_text_block(
    text: str,
    wrap_limits: list[int],
    size_candidates: list[int],
    max_lines: int,
    prefer_single_mixed_short: bool = False,
) -> tuple[list[str], int]:
    if not text:
        return [], size_candidates[-1] if size_candidates else 16
    mixed = bool(re.search(r"[\u4e00-\u9fff]", text) and re.search(r"[A-Za-z]", text))
    compact_text = re.sub(r"\s+", "", text)
    if prefer_single_mixed_short and mixed and len(compact_text) <= 18:
        return [text], size_candidates[-1] if size_candidates else 16
    best_lines: list[str] | None = None
    best_size = size_candidates[-1] if size_candidates else 16
    for limit in wrap_limits:
        lines = _wrap_text(text, limit)
        for size in size_candidates:
            if len(lines) <= max_lines:
                return lines, size
        if best_lines is None or len(lines) < len(best_lines):
            best_lines = lines
    return (best_lines or _wrap_text(text, wrap_limits[-1]), best_size)


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


def _derive_info_copy(prompt: str, mode: str = "infographic") -> dict[str, Any]:
    if _looks_like_article_prompt(prompt):
        return _derive_article_copy(prompt, mode=mode)
    title = _extract_labeled_value(prompt, ["标题", "主标题", "title"]) or "信息图概览"
    subtitle = _extract_labeled_value(prompt, ["副标题", "subtitle"]) or "清晰层级 / 重点突出 / 本地生成"
    kicker = _extract_labeled_value(prompt, ["角标", "badge"]) or ("TEXT COVER" if mode == "text_cover" else "INFOGRAPHIC")
    emphasis = _extract_labeled_value(prompt, ["核心数字", "重点数字", "highlight"]) or "3"
    bullets = _parse_bullets(prompt)
    if not bullets:
        bullets = ["信息层级清晰", "重点数字突出", "适合封面与知识卡片", "本地 SVG 到 PNG 导出"]
    return {
        "title": title,
        "subtitle": subtitle,
        "kicker": kicker,
        "emphasis": emphasis,
        "bullets": bullets[:6],
    }


def _split_bullet_copy(text: str) -> tuple[str, str]:
    if "：" in text:
        left, right = text.split("：", 1)
        return left.strip(), right.strip()
    if ":" in text:
        left, right = text.split(":", 1)
        return left.strip(), right.strip()
    compact = text.strip()
    if re.search(r"[\u4e00-\u9fff]", compact):
        if len(compact) > 8:
            return compact[:6], compact[6:]
    else:
        words = compact.split()
        if len(words) > 3:
            return " ".join(words[:3]), " ".join(words[3:])
    return compact, "提炼重点信息，保持清晰易读。"


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
    sections = _parse_article_sections(prompt)
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
    sections = _parse_article_sections(prompt)
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
        body_lines = [line for line in section["lines"] if len(line) >= 6][:6]
        if not body_lines:
            continue
        title = heading
        subtitle = body_lines[0][:28]
        emphasis = _pick_stat_phrase("\n".join([heading, *body_lines])) or article["emphasis"]
        section_kind = _infer_section_kind(heading, body_lines)
        card_prompt = _story_card_prompt_for_kind(title, subtitle, emphasis, body_lines, heading, section_kind)
        if resolved_strategy == "story" and card_index == 2:
            card_prompt = f"文字封面 标题：{title} 副标题：{subtitle} 核心数字：{emphasis}"
            section_kind = "text_cover"
        elif resolved_strategy == "visual" and any(token in heading for token in ["公告", "数据"]):
            card_prompt = f"文字封面 标题：{title} 副标题：{subtitle} 核心数字：{emphasis}"
            section_kind = "text_cover"
        stem = f"{card_index:02d}-{_slugify(heading)[:24]}"
        cards.append(
            {
                "index": card_index,
                "heading": heading,
                "kind": section_kind,
                "title": title,
                "subtitle": subtitle,
                "emphasis": emphasis,
                "bullets": body_lines[:5],
                "stem": stem,
                "prompt": card_prompt,
            }
        )
        card_index += 1
        if card_index > 6:
            break

    return analysis, cards


def generate_article_story(
    prompt: str,
    output_dir: str | Path,
    width: int,
    height: int,
    strategy: str = "auto",
    mode: str = "all",
) -> dict[str, Any]:
    story_dir = Path(output_dir).expanduser().resolve()
    story_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = story_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    analysis, cards = _build_story_cards(prompt, strategy=strategy)
    resolved_strategy = analysis["strategy"]
    analysis_path = story_dir / "analysis.json"
    outline_path = story_dir / "outline.md"
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outline_path.write_text(_render_outline_md(analysis), encoding="utf-8")
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
            results.append(
                generate_image(
                    card["prompt"],
                    story_dir / f"{card['stem']}.png",
                    width,
                    height,
                    story_dir / f"{card['stem']}.svg",
                )
            )

    return {
        "mode": "article-story-local",
        "output_dir": str(story_dir),
        "strategy": resolved_strategy,
        "analysis": str(analysis_path),
        "outline": str(outline_path),
        "prompts_dir": str(prompts_dir),
        "count": len(cards),
        "generated_count": len(results),
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
    seed = _stable_int(prompt)
    focus_token = _extract_focus_token(copy["title"])
    is_tall = (height / max(width, 1)) >= 1.35
    lower_title = copy["title"].lower()
    if any(token in lower_title for token in ["为什么", "为啥", "how", "why"]):
        variant = "note"
    else:
        variant = "quote" if focus_token else ("note" if seed % 2 else "quote")

    if variant == "quote":
        bg = "#F2ECFA"
        ink = "#3E384D"
        accent = "#FFBF47"
        soft = "#DBCDF4"
        quote_size = max(64, int(width * 0.11))
        title_lines, title_size = _fit_text_block(
            copy["title"],
            [12, 10, 8, 7] if re.search(r"[\u4e00-\u9fff]", copy["title"]) else [20, 18, 16],
            [max(54, int(width * 0.094)), max(48, int(width * 0.082)), max(42, int(width * 0.072))],
            3,
            prefer_single_mixed_short=True,
        )
        subtitle_lines, subtitle_size = _fit_text_block(
            copy["subtitle"],
            [20, 16, 14] if re.search(r"[\u4e00-\u9fff]", copy["subtitle"]) else [30, 26, 22],
            [max(22, int(width * 0.028)), max(20, int(width * 0.025)), max(18, int(width * 0.022))],
            2,
        )
        highlight_width = width * (0.30 if focus_token else 0.18)
        title_y = height * (0.42 if is_tall else 0.46)
        subtitle_y = min(height * 0.84, title_y + _text_block_height(title_lines, title_size, 1.08) + height * 0.10)
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{bg}"/>
  <text x="{width*0.12:.2f}" y="{height*0.18:.2f}" font-family="Georgia, Times New Roman, serif" font-size="{quote_size}" font-weight="900" fill="{soft}">“</text>
  <text x="{width*0.19:.2f}" y="{height*0.18:.2f}" font-family="Georgia, Times New Roman, serif" font-size="{quote_size}" font-weight="900" fill="{soft}">“</text>
  <rect x="{width*0.40:.2f}" y="{height*(0.43 if is_tall else 0.47):.2f}" width="{highlight_width:.2f}" height="{height*0.03:.2f}" fill="{accent}"/>
  {_svg_text_block(width*0.12, title_y, title_lines, title_size, ink, weight=900, line_gap=1.08)}
  {_svg_text_block(width*0.12, subtitle_y, subtitle_lines[:2], subtitle_size, "#6C6680", weight=700, line_gap=1.18)}
  <rect x="{width*0.82:.2f}" y="{height*0.92:.2f}" width="{width*0.08:.2f}" height="{height*0.012:.2f}" fill="{soft}"/>
</svg>'''

    card_bg = "#5B82F4"
    paper = "#FFFDF8"
    shadow = "#C7D5FF"
    ink = "#121212"
    meta = "#5B82F4"
    emoji = "🤔" if "为什么" in copy["title"] or "为啥" in copy["title"] else "..."
    paper_x = width * 0.08
    paper_y = height * 0.08
    paper_w = width * 0.84
    paper_h = height * 0.84
    title_lines, title_size = _fit_text_block(
        copy["title"],
        [12, 10, 8] if re.search(r"[\u4e00-\u9fff]", copy["title"]) else [18, 16, 14],
        [max(48, int(width*(0.102 if is_tall else 0.092))), max(42, int(width*(0.09 if is_tall else 0.082))), max(36, int(width*0.074))],
        4,
        prefer_single_mixed_short=True,
    )
    title_y = height*(0.38 if is_tall else 0.44)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="{card_bg}"/>
  <rect x="{paper_x + width*0.03:.2f}" y="{paper_y - height*0.01:.2f}" width="{paper_w:.2f}" height="{paper_h:.2f}" rx="{width*0.05:.2f}" fill="{shadow}"/>
  <rect x="{paper_x:.2f}" y="{paper_y:.2f}" width="{paper_w:.2f}" height="{paper_h:.2f}" rx="{width*0.05:.2f}" fill="{paper}"/>
  {_svg_text_block(width*0.16, height*0.16, [emoji], max(34, int(width*0.07)), ink, weight=700)}
  {_svg_text_block(width*0.18, height*0.20, ["..."], max(18, int(width*0.03)), meta, weight=800)}
  {_svg_text_block(width*0.72, height*0.18, [copy["kicker"].title() if copy["kicker"] else "Text Note"], max(16, int(width*0.026)), meta, weight=800)}
  {_svg_text_block(width*0.14, title_y, title_lines, title_size, ink, weight=900, line_gap=1.08)}
  <path d="M {width*0.14:.2f} {height*0.86:.2f} L {width*0.82:.2f} {height*0.86:.2f}" stroke="{meta}" stroke-width="{max(3, int(width*0.0025))}"/>
</svg>'''


def _compose_infographic_svg(prompt: str, width: int, height: int) -> str:
    copy = _derive_info_copy(prompt, mode="infographic")
    kind = _infer_infographic_kind(prompt)
    title_lines, title_size = _fit_text_block(
        copy["title"],
        [12, 10, 8] if re.search(r"[\u4e00-\u9fff]", copy["title"]) else [20, 18, 16],
        [max(32, int(width*0.048)), max(28, int(width*0.042)), max(24, int(width*0.038))],
        3,
        prefer_single_mixed_short=True,
    )
    subtitle_lines, subtitle_size = _fit_text_block(
        copy["subtitle"],
        [18, 16, 14] if re.search(r"[\u4e00-\u9fff]", copy["subtitle"]) else [30, 26, 22],
        [max(16, int(width*0.02)), max(15, int(width*0.019)), max(14, int(width*0.017))],
        2,
    )
    bullets = copy["bullets"][:]

    if kind == "map":
        zones = bullets[:3] or [
            "编码代理：Claude Code、Codex、Gemini CLI，强调终端执行与代理能力",
            "AI IDE：Cursor、Windsurf、GitHub Copilot，强调上下文与协作",
            "云端开发与应用生成：Replit、Lovable、Bolt.new，强调原型与部署",
        ]
        zone_y = [height * 0.30, height * 0.50, height * 0.70]
        zone_h = height * 0.14
        colors = [("#EAF0FF", "#6B74D8"), ("#F8EEFF", "#C75BCE"), ("#ECFFF5", "#32A56A")]
        blocks: list[str] = []
        for idx, item in enumerate(zones):
            heading, desc = _split_bullet_copy(item)
            y = zone_y[idx]
            bg_fill, accent = colors[idx % len(colors)]
            blocks.append(f'<rect x="{width*0.08:.2f}" y="{y:.2f}" width="{width*0.84:.2f}" height="{zone_h:.2f}" rx="24" fill="{bg_fill}"/>')
            blocks.append(f'<rect x="{width*0.10:.2f}" y="{y + zone_h*0.18:.2f}" width="{width*0.012:.2f}" height="{zone_h*0.62:.2f}" rx="8" fill="{accent}"/>')
            blocks.append(_svg_text_block(width*0.15, y + zone_h*0.33, _wrap_text(heading, 12 if re.search(r"[\u4e00-\u9fff]", heading) else 18), max(20, int(width*0.026)), "#243047", weight=900, line_gap=1.05))
            blocks.append(_svg_text_block(width*0.15, y + zone_h*0.63, _wrap_text(desc, 28 if re.search(r"[\u4e00-\u9fff]", desc) else 40), max(14, int(width*0.018)), "#667089", weight=700, line_gap=1.08))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#F5F6FC"/>
  <rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.24:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="#EEF2FF"/>
  {_svg_text_block(width*0.10, height*0.105, [copy["kicker"] or "产品地图"], max(14, int(width*0.017)), "#6B74D8", weight=800)}
  {_svg_text_block(width*0.08, height*0.16, title_lines, title_size, "#243047", weight=900, line_gap=1.04)}
  {_svg_text_block(width*0.08, height*0.22, subtitle_lines[:2], subtitle_size, "#7E869B", weight=700, line_gap=1.08)}
  <rect x="{width*0.08:.2f}" y="{height*0.25:.2f}" width="{width*0.12:.2f}" height="{height*0.04:.2f}" rx="16" fill="#F2EEFF"/>
  {_svg_text_block(width*0.11, height*0.276, [copy["emphasis"]], max(18, int(width*0.022)), "#7A59E6", weight=900)}
  <g>{''.join(blocks)}</g>
  {_svg_text_block(width*0.50, height*0.94, ["按产品形态看清当前 Vibe Coding 版图"], max(14, int(width*0.018)), "#A7ADBF", weight=600, anchor="middle")}
</svg>'''

    if kind == "catalog":
        mixed_title = bool(re.search(r"[\u4e00-\u9fff]", copy["title"]) and re.search(r"[A-Za-z]", copy["title"]))
        compact_title = re.sub(r"\s+", "", copy["title"])
        if mixed_title and len(compact_title) <= 18:
            catalog_title_lines = [copy["title"]]
        else:
            catalog_title_lines = _wrap_text(copy["title"], 10 if mixed_title else 6 if re.search(r"[\u4e00-\u9fff]", copy["title"]) else 14)
        catalog_subtitle_lines = subtitle_lines[:2]
        catalog_title_size = max(26, int(width*0.041)) if len(catalog_title_lines) == 1 else max(30, int(width*0.046))
        catalog_title_y = height * 0.16
        catalog_subtitle_y = catalog_title_y + len(catalog_title_lines) * catalog_title_size * 1.02 + height * 0.02
        catalog_badge_y = catalog_subtitle_y + max(1, len(catalog_subtitle_lines)) * max(15, int(width*0.019)) * 1.08 + height * 0.025
        rows = bullets[:6] or ["Cursor / AI IDE / Agent 与代码库上下文", "Windsurf / Agent IDE / 流程驱动与协作", "GitHub Copilot / 编程助手 / 生态广上手快"]
        row_h, row_gap = _tight_row_metrics(height, catalog_badge_y + height * 0.042, height * 0.11, len(rows))
        cards: list[str] = []
        start_y = catalog_badge_y + height * 0.03
        colors = ["#6F67DE", "#F06AB2", "#35C5F2", "#43E39B", "#FFB84D", "#8B4DB4"]
        for idx, row in enumerate(rows):
            y = start_y + idx * (row_h + row_gap)
            name, role, desc = _split_catalog_row(row)
            cards.append(f'<rect x="{width*0.07:.2f}" y="{y:.2f}" width="{width*0.86:.2f}" height="{row_h*0.74:.2f}" rx="18" fill="#FFFFFF"/>')
            cards.append(f'<circle cx="{width*0.12:.2f}" cy="{y + row_h*0.25:.2f}" r="{width*0.022:.2f}" fill="{colors[idx % len(colors)]}"/>')
            cards.append(_svg_text_block(width*0.17, y + row_h*0.23, [name], max(17, int(width*0.023)), "#2A2F45", weight=900))
            cards.append(_svg_text_block(width*0.17, y + row_h*0.44, _wrap_text(role, 16 if re.search(r"[\u4e00-\u9fff]", role) else 22), max(13, int(width*0.017)), "#6A73D8", weight=800, line_gap=1.03))
            cards.append(_svg_text_block(width*0.52, y + row_h*0.29, _wrap_text(desc, 20 if re.search(r"[\u4e00-\u9fff]", desc) else 28), max(13, int(width*0.017)), "#667089", weight=700, line_gap=1.05))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#F5F6FC"/>
  <rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.26:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="#EEF2FF"/>
  {_svg_text_block(width*0.10, height*0.105, [copy["kicker"] or "工具速览"], max(14, int(width*0.017)), "#6B74D8", weight=800)}
  {_svg_text_block(width*0.07, catalog_title_y, catalog_title_lines, catalog_title_size, "#243047", weight=900, line_gap=1.02)}
  {_svg_text_block(width*0.07, catalog_subtitle_y, catalog_subtitle_lines, max(15, int(width*0.019)), "#7E869B", weight=700, line_gap=1.08)}
  <rect x="{width*0.07:.2f}" y="{catalog_badge_y:.2f}" width="{width*0.16:.2f}" height="{height*0.042:.2f}" rx="18" fill="#F2EEFF"/>
  {_svg_text_block(width*0.10, catalog_badge_y + height*0.028, [copy["emphasis"]], max(18, int(width*0.022)), "#7A59E6", weight=900)}
  <g>{''.join(cards)}</g>
  {_svg_text_block(width*0.50, height*0.95, ["主流产品定位、特点和适用场景"], max(14, int(width*0.018)), "#A7ADBF", weight=600, anchor="middle")}
</svg>'''

    if kind == "qa":
        qa_items = bullets[:4] or ["问题定义：先说结论，再拆原因", "核心机制：把复杂概念拆成 3 个点", "关键数据：用数字做视觉锚点", "落地建议：最后给出行动结论"]
        cards: list[str] = []
        for idx, item in enumerate(qa_items):
            y = height * (0.28 + idx * 0.14)
            q, a = _split_bullet_copy(item)
            cards.append(f'<rect x="{width*0.08:.2f}" y="{y:.2f}" width="{width*0.84:.2f}" height="{height*0.11:.2f}" rx="22" fill="#FFFFFF"/>')
            cards.append(f'<circle cx="{width*0.13:.2f}" cy="{y + height*0.04:.2f}" r="{width*0.025:.2f}" fill="#E7E9FF"/>')
            cards.append(_svg_text_block(width*0.13, y + height*0.048, [f"Q{idx + 1}"], max(14, int(width*0.017)), "#6A73D8", weight=900, anchor="middle"))
            cards.append(_svg_text_block(width*0.18, y + height*0.045, _wrap_text(q, 14 if re.search(r"[\u4e00-\u9fff]", q) else 20), max(17, int(width*0.022)), "#22263A", weight=900, line_gap=1.05))
            cards.append(_svg_text_block(width*0.18, y + height*0.080, _wrap_text(a, 22 if re.search(r"[\u4e00-\u9fff]", a) else 34), max(14, int(width*0.018)), "#7E869B", weight=700, line_gap=1.1))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#F5F6FC"/>
  <rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.24:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="#EEF2FF"/>
  {_svg_text_block(width*0.10, height*0.105, [copy["kicker"] or "问答卡"], max(14, int(width*0.017)), "#6B74D8", weight=800)}
  {_svg_text_block(width*0.08, height*0.17, title_lines, max(30, int(width*0.046)), "#243047", weight=900, line_gap=1.06)}
  {_svg_text_block(width*0.08, height*0.23, subtitle_lines[:2], max(15, int(width*0.019)), "#7E869B", weight=700, line_gap=1.08)}
  <g>{''.join(cards)}</g>
  {_svg_text_block(width*0.50, height*0.94, ["问题拆清楚，图片就更有表达力"], max(14, int(width*0.018)), "#A7ADBF", weight=600, anchor="middle")}
</svg>'''

    if kind == "timeline":
        points = bullets[:5] or ["提出概念", "官方定名", "行业采用", "规模增长", "共识形成"]
        nodes: list[str] = []
        base_y = height * 0.36
        spacing = width * 0.18
        start_x = width * 0.14
        nodes.append(f'<path d="M {start_x:.2f} {base_y:.2f} L {start_x + spacing*(len(points)-1):.2f} {base_y:.2f}" stroke="#C9D0EA" stroke-width="4" stroke-linecap="round"/>')
        colors = ["#6F67DE", "#F06AB2", "#35C5F2", "#43E39B", "#FFB84D"]
        for idx, item in enumerate(points):
            x = start_x + spacing * idx
            nodes.append(f'<circle cx="{x:.2f}" cy="{base_y:.2f}" r="{width*0.028:.2f}" fill="{colors[idx % len(colors)]}"/>')
            nodes.append(_svg_text_block(x, base_y + height*0.11, _wrap_text(item, 8 if re.search(r"[\u4e00-\u9fff]", item) else 12), max(15, int(width*0.019)), "#394156", weight=800, anchor="middle", line_gap=1.08))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#F5F6FC"/>
  <rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.20:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="#EEF2FF"/>
  {_svg_text_block(width*0.10, height*0.105, [copy["kicker"] or "时间线"], max(14, int(width*0.017)), "#6B74D8", weight=800)}
  {_svg_text_block(width*0.08, height*0.18, title_lines, max(30, int(width*0.046)), "#243047", weight=900, line_gap=1.06)}
  {_svg_text_block(width*0.08, height*0.25, subtitle_lines[:2], max(15, int(width*0.019)), "#7E869B", weight=700, line_gap=1.08)}
  <g>{''.join(nodes)}</g>
  <rect x="{width*0.08:.2f}" y="{height*0.68:.2f}" width="{width*0.84:.2f}" height="{height*0.14:.2f}" rx="24" fill="#FFFFFF"/>
  {_svg_text_block(width*0.12, height*0.73, _wrap_text(copy["emphasis"], 10), max(22, int(width*0.03)), "#7A59E6", weight=900)}
  {_svg_text_block(width*0.28, height*0.73, subtitle_lines[:2], max(15, int(width*0.019)), "#7E869B", weight=700, line_gap=1.08)}
</svg>'''

    if kind == "comparison":
        rows = bullets[:5] or ["以前：手动整理", "现在：自动筛选", "以前：逐条处理", "现在：结果直达"]
        row_h = height * 0.11
        body: list[str] = []
        start_y = height * 0.32
        comparison_title = _wrap_text(copy["title"], 14 if re.search(r"[\u4e00-\u9fff]", copy["title"]) else 24)
        for idx, row in enumerate(rows):
            y = start_y + idx * row_h
            scene, before, after = _split_comparison_row(row)
            body.append(f'<rect x="{width*0.07:.2f}" y="{y:.2f}" width="{width*0.86:.2f}" height="{row_h*0.92:.2f}" rx="18" fill="#FFFFFF" fill-opacity="0.80"/>')
            body.append(_svg_text_block(width*0.10, y + row_h*0.34, _wrap_text(scene, 8 if re.search(r"[\u4e00-\u9fff]", scene) else 14), max(17, int(width*0.021)), "#2A2F45", weight=800, line_gap=1.1))
            body.append(_svg_text_block(width*0.34, y + row_h*0.30, _wrap_text(before, 10 if re.search(r"[\u4e00-\u9fff]", before) else 16), max(15, int(width*0.018)), "#41485F", weight=700, line_gap=1.12))
            body.append(_svg_text_block(width*0.62, y + row_h*0.30, _wrap_text(after, 10 if re.search(r"[\u4e00-\u9fff]", after) else 16), max(15, int(width*0.018)), "#657DE8", weight=800, line_gap=1.12))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#F5F6FC"/>
  <rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.86:.2f}" height="{height*0.035:.2f}" rx="{height*0.017:.2f}" fill="url(#bar)"/>
  <defs>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#5B82F4"/>
      <stop offset="100%" stop-color="#8B4DB4"/>
    </linearGradient>
  </defs>
  {_svg_text_block(width*0.09, height*0.105, [copy["kicker"] or "前后对比"], max(14, int(width*0.017)), "#FFFFFF", weight=800)}
  {_svg_text_block(width*0.07, height*0.18, comparison_title, max(28, int(width*0.04)), "#5B6AD6", weight=900, line_gap=1.04)}
  <rect x="{width*0.07:.2f}" y="{height*0.24:.2f}" width="{width*0.86:.2f}" height="{height*0.06:.2f}" rx="18" fill="#7C63D8"/>
  {_svg_text_block(width*0.10, height*0.275, ["场景"], max(16, int(width*0.02)), "#FFFFFF", weight=800)}
  {_svg_text_block(width*0.34, height*0.275, ["以前"], max(16, int(width*0.02)), "#FFFFFF", weight=800)}
  {_svg_text_block(width*0.62, height*0.275, ["现在"], max(16, int(width*0.02)), "#FFFFFF", weight=800)}
  <g>{''.join(body)}</g>
  {_svg_text_block(width*0.50, height*0.94, [copy["subtitle"]], max(14, int(width*0.018)), "#9AA0B5", weight=600, anchor="middle")}
</svg>'''

    if kind == "flow":
        steps = bullets[:5] or ["写完文章", "Agent 唤醒", "自动翻译", "推送发布", "状态更新"]
        step_h = height * 0.11
        nodes: list[str] = []
        arrows: list[str] = []
        for idx, step in enumerate(steps):
            y = height * 0.24 + idx * step_h
            circle_colors = ["#6F67DE", "#F06AB2", "#35C5F2", "#43E39B", "#FFB84D"]
            nodes.append(f'<rect x="{width*0.12:.2f}" y="{y:.2f}" width="{width*0.78:.2f}" height="{step_h*0.72:.2f}" rx="22" fill="#FFFFFF"/>')
            nodes.append(f'<circle cx="{width*0.17:.2f}" cy="{y + step_h*0.36:.2f}" r="{width*0.038:.2f}" fill="{circle_colors[idx % len(circle_colors)]}"/>')
            nodes.append(_svg_text_block(width*0.17, y + step_h*0.39, [str(idx + 1)], max(18, int(width*0.022)), "#FFFFFF", weight=900, anchor="middle"))
            title, desc = _split_bullet_copy(step)
            nodes.append(_svg_text_block(width*0.25, y + step_h*0.30, [title], max(18, int(width*0.026)), "#22263A", weight=800))
            nodes.append(_svg_text_block(width*0.25, y + step_h*0.53, _wrap_text(desc, 18 if re.search(r"[\u4e00-\u9fff]", desc) else 28), max(14, int(width*0.018)), "#8A90A8", weight=700, line_gap=1.1))
            if idx < len(steps) - 1:
                arrows.append(f'<path d="M {width*0.50:.2f} {y + step_h*0.73:.2f} L {width*0.50:.2f} {y + step_h*0.94:.2f}" stroke="#CBD2EA" stroke-width="3" stroke-linecap="round"/>')
                arrows.append(_svg_text_block(width*0.50, y + step_h*0.95, ["↓"], max(18, int(width*0.024)), "#B9BED2", weight=700, anchor="middle"))
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#F5F6FC"/>
  <rect x="{width*0.07:.2f}" y="{height*0.075:.2f}" width="{width*0.54:.2f}" height="{height*0.04:.2f}" rx="{height*0.02:.2f}" fill="#E6EBFF"/>
  {_svg_text_block(width*0.10, height*0.103, [copy["kicker"] or "自动流程"], max(14, int(width*0.017)), "#6A73D8", weight=800)}
  {_svg_text_block(width*0.07, height*0.10, [copy["title"]], max(30, int(width*0.045)), "#29304C", weight=900)}
  {_svg_text_block(width*0.07, height*0.145, subtitle_lines, max(16, int(width*0.02)), "#8A90A8", weight=700, line_gap=1.08)}
  <g>{''.join(nodes)}</g>
  <g>{''.join(arrows)}</g>
  {_svg_text_block(width*0.50, height*0.95, ["发财 · AI效率干货 · 收藏备用"], max(14, int(width*0.018)), "#A7ADBF", weight=600, anchor="middle")}
</svg>'''

    cards: list[str] = []
    mechanism_items = bullets[:3] or ["读到结构快照", "页面可持续读取", "同一任务链保留上下文"]
    mechanism_subtitle_lines = _wrap_text(copy["subtitle"], 22 if re.search(r"[\u4e00-\u9fff]", copy["subtitle"]) else 34)[:2]
    card_y = [height * 0.33, height * 0.50, height * 0.67]
    colors = ["#5B82F4", "#E284F1", "#4AA6F0"]
    for idx, item in enumerate(mechanism_items):
        y = card_y[idx]
        cards.append(f'<rect x="{width*0.11:.2f}" y="{y:.2f}" width="{width*0.78:.2f}" height="{height*0.12:.2f}" rx="16" fill="#FFFFFF"/>')
        cards.append(f'<rect x="{width*0.125:.2f}" y="{y + height*0.018:.2f}" width="{width*0.010:.2f}" height="{height*0.072:.2f}" rx="6" fill="{colors[idx % len(colors)]}"/>')
        cards.append(_svg_text_block(width*0.16, y + height*0.05, _wrap_text(item, 18 if re.search(r"[\u4e00-\u9fff]", item) else 28), max(18, int(width*0.026)), "#394156", weight=800, line_gap=1.12))
        if idx < len(mechanism_items) - 1:
            cards.append(f'<path d="M {width*0.13:.2f} {y + height*0.12:.2f} L {width*0.86:.2f} {y + height*0.12:.2f}" stroke="#EEF1F6" stroke-width="2"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#F5F6FC"/>
  <rect x="{width*0.07:.2f}" y="{height*0.08:.2f}" width="{width*0.86:.2f}" height="{height*0.78:.2f}" rx="36" fill="#FFFDF8"/>
  <rect x="{width*0.11:.2f}" y="{height*0.105:.2f}" width="{width*0.18:.2f}" height="{height*0.036:.2f}" rx="{height*0.018:.2f}" fill="#EEF2FF"/>
  {_svg_text_block(width*0.14, height*0.130, [copy["kicker"] or "机制卡"], max(14, int(width*0.017)), "#6B74D8", weight=800)}
  {_svg_text_block(width*0.11, height*0.21, title_lines, max(30, int(width*0.047)), "#253044", weight=900, line_gap=1.08)}
  <rect x="{width*0.11:.2f}" y="{height*0.255:.2f}" width="{width*0.22:.2f}" height="{height*0.055:.2f}" rx="{height*0.02:.2f}" fill="#F2EEFF"/>
  {_svg_text_block(width*0.14, height*0.290, [copy["emphasis"]], max(20, int(width*0.028)), "#7A59E6", weight=900)}
  {_svg_text_block(width*0.36, height*0.290, mechanism_subtitle_lines, max(15, int(width*0.02)), "#7E869B", weight=700, line_gap=1.08)}
  <g>{''.join(cards)}</g>
  {_svg_text_block(width*0.13, height*0.80, ["收藏备用，下次直接照着做"], max(15, int(width*0.02)), "#7E869B", weight=700)}
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
    parser.add_argument("--prompt", help="Text prompt")
    parser.add_argument("--prompt-file", help="Read prompt/article text from local file")
    parser.add_argument("--output", help="Output PNG path")
    parser.add_argument("--svg-output", help="Output SVG path (optional)")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--openclaw-project", help="Generate assets/thumbnail+icon for OpenClaw project")
    parser.add_argument("--story-output-dir", help="Generate a multi-image article story set into this directory")
    parser.add_argument("--story-strategy", choices=["auto", "story", "dense", "visual"], default="auto", help="Story strategy for article-to-image sets")
    parser.add_argument("--outline-only", action="store_true", help="Write analysis and outline only")
    parser.add_argument("--prompts-only", action="store_true", help="Write analysis, outline, and prompt files only")
    parser.add_argument("--images-only", action="store_true", help="Generate images using existing or regenerated prompt files")
    args = parser.parse_args(argv)
    if not args.prompt and not args.prompt_file:
        parser.error("one of --prompt or --prompt-file is required")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).expanduser().read_text(encoding="utf-8")

    try:
        if args.openclaw_project:
            result = generate_openclaw_assets(args.openclaw_project, prompt)
        elif args.story_output_dir:
            story_mode = "all"
            if args.outline_only:
                story_mode = "outline-only"
            elif args.prompts_only:
                story_mode = "prompts-only"
            elif args.images_only:
                story_mode = "images-only"
            result = generate_article_story(prompt, args.story_output_dir, args.width, args.height, strategy=args.story_strategy, mode=story_mode)
        else:
            output = args.output
            if not output:
                stem = _slugify(prompt)[:48]
                output = str(Path.cwd() / f"{stem}.png")
            result = generate_image(prompt, output, args.width, args.height, args.svg_output)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

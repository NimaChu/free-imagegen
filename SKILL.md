---
name: free-imagegen
description: Fully local free text-to-image skill for OpenClaw and general assets. Generates SVG from prompt, then converts SVG to PNG with local tools only (no online API calls).
---

# Free ImageGen

纯本地免费流程：`Prompt -> SVG -> PNG`。  
默认是通用插画创作，不限制在封面场景。

## Quick Flow

1. 输入 prompt 与尺寸（主题、角色、场景、氛围、细节都可以描述）。
2. 运行脚本生成 SVG。
3. 用本地渲染器转为 PNG。
4. OpenClaw 项目可一键生成 `assets/thumbnail` 与 `assets/icon`。
5. 如果输入的是长文章，可自动拆成多张图文卡片。

## Composition Modes

- `illustration`（默认）：
  - 普通绘图请求走这个模式（人物、物体、场景）
- `infographic`（按关键词触发）：
  - 当 prompt 出现 `信息图 / infographic / 知识卡片 / 图解 / 对比图 / 时间线 / 流程图 / 架构图`
  - 适合高信息密度、卡片分区、重点数字展示
  - 长文章输入也会自动优先走这个模式
- `text_cover`（按关键词触发）：
  - 当 prompt 出现 `文字封面 / text cover / title card / 文字海报 / 标题页`
  - 适合大标题主导、少图形干扰的文字封面
- `cover`（按关键词触发）：
  - 当 prompt 明确出现 `封面/海报/thumbnail/cover` 时触发
  - 适合宣传图或商店图

## Main Commands

单图生成：

```bash
python3 scripts/free_image_gen.py \
  --prompt "海底龙虾海报，左上角写NimaTech，底部大标题十三香小龙虾，红色龙虾，画面更热闹有气泡和光感" \
  --output /absolute/path/output/lobster.png \
  --svg-output /absolute/path/output/lobster.svg \
  --width 1024 \
  --height 1024
```

信息图生成：

```bash
python3 scripts/free_image_gen.py \
  --prompt "AI 编码工作流信息图，标题 GPT-5.4 Coding Workflow，副标题 从需求到提交，核心数字 4，1. 需求理解 2. 代码实现 3. 验证测试 4. 提交发布" \
  --output /absolute/path/output/workflow-infographic.png \
  --svg-output /absolute/path/output/workflow-infographic.svg \
  --width 1080 \
  --height 1440
```

文章转图文卡组：

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --story-strategy dense \
  --width 1080 \
  --height 1440
```

输出内容：

- `analysis.json`
- `outline.md`
- `prompts/*.md`
- `01-cover.png/svg`
- `02-*.png/svg` 到 `06-*.png/svg`
- 自动按章节拆成封面图、公告卡、数据卡、原因卡等
- 支持 `auto / story / dense / visual` 四种卡组策略

只生成分析、大纲和 prompt：

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --prompts-only
```

只根据已有卡组流程生成图片：

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --images-only
```

文字封面图生成：

```bash
python3 scripts/free_image_gen.py \
  --prompt "文字封面，标题 AI 产品设计原则，副标题 清晰层级 高信息密度 强识别度，核心数字 07" \
  --output /absolute/path/output/text-cover.png \
  --svg-output /absolute/path/output/text-cover.svg \
  --width 1080 \
  --height 1440
```

OpenClaw 资产一键生成：

```bash
python3 scripts/free_image_gen.py \
  --prompt "space heist arcade lobster game" \
  --openclaw-project /absolute/path/to/your-openclaw-app
```

输出内容：

- `assets/thumbnail.svg` + `assets/thumbnail.png`
- `assets/icon.svg` + `assets/icon.png`
- 自动更新 `manifest.json` 的 `thumbnail/icon` 字段（若存在）

## Prompt 引导建议

- 直接描述你要画的内容，不需要参数化配置。
- 做信息图时，尽量把标题、副标题、核心数字和要点都直接写进 prompt。
- 做文章转图时，优先提供纯正文文本：
  - 保留标题、段落、列表、表格内容
  - 去掉原文中的配图说明或图片占位
- 如果你知道内容更偏哪种表达，可以主动指定：
  - `--story-strategy story`
  - `--story-strategy dense`
  - `--story-strategy visual`
- 做文字封面时，明确写 `文字封面` 或 `title card`，这样会启用更强的排版模式。
- 把你想要的文案直接写进 prompt（如果需要上字），例如：
  - `左上角写 NimaTech`
  - `底部大标题 十三香小龙虾`
- 把主体和色彩写进 prompt，例如：
  - `红色龙虾`
  - `清新梦幻插画风，柔和光影`
- 让 agent 自主补充细节，例如：
  - `请丰富背景层次、光影和装饰元素`

人物示例：

`长发可爱女生，清新梦幻插画风，柔和光影，细节丰富`

## HTTP Service

启动服务：

```bash
python3 scripts/free_image_http_service.py --host 127.0.0.1 --port 8787
```

健康检查：

```bash
curl http://127.0.0.1:8787/health
```

单图生成：

```bash
curl -X POST http://127.0.0.1:8787/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt":"海底龙虾海报，左上角写NimaTech，底部大标题十三香小龙虾，红色龙虾，增强光影和气泡细节",
    "width":1024,
    "height":1024,
    "output":"/absolute/path/output/lobster.png",
    "svg_output":"/absolute/path/output/lobster.svg"
  }'
```

OpenClaw 资产生成：

```bash
curl -X POST http://127.0.0.1:8787/openclaw-assets \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt":"space lobster game cover",
    "project":"/absolute/path/to/openclaw-project"
  }'
```

## Files

- `scripts/free_image_gen.py`: 本地 SVG 生成 + PNG 导出核心
- `scripts/free_image_http_service.py`: 本地 HTTP 封装
- `references/providers.md`: 本地渲染链路说明

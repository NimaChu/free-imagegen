# Free ImageGen

[English README](./README.md)

一个 **免 API、没硬件门槛、纯本地** 的内容型生图技能。

如果你想直接生成：
- 📱 小红书封面
- 📊 知识卡 / 信息图
- 📰 文章转图文卡组
- 🦞 OpenClaw 可直接使用的视觉资产

它通常会比扩散模型更顺手。

## 为什么会有这个技能？

大多数文生图工具更擅长：
- 写实感
- 氛围感
- 视觉奇观
- “一句话生成一张看起来很厉害的图”

`Free ImageGen` 走的是另一条路：
- ✅ **免 API**：不需要图片 API，不需要按张付费
- ✅ **没硬件门槛**：不用 GPU，不用本地部署扩散模型
- ✅ **纯本地**：更适合隐私、可控、低成本工作流
- ✅ **自由度高**：agent 可以自己决定分页、版式、风格
- ✅ **中文友好**：中文标题、中英混排、手机阅读更稳
- ✅ **小红书友好**：特别适合封面、知识卡、文章图组

如果你想做的是 **内容表达型图片**，而不是写实绘画，这条路通常会比扩散模型更稳。

## 它和扩散模型有什么不同？

扩散模型适合：
- 写实插画
- 电影感 / 绘画感
- 视觉冲击
- 细节非常丰富的自由绘图

`Free ImageGen` 更适合：
- 结构化内容表达
- 可读的文章页面
- 清单、对比、机制、地图、QA 这类知识卡
- 一篇文章直接产出一整套图片
- agent 负责判断，renderer 负责稳定执行

一句话说：

> 它更像一个面向内容工作流的本地设计渲染器，而不是一个追求视觉奇观的扩散模型。

## 推荐使用场景

### 1. 小红书封面
适合：
- 大标题封面
- 观点封面
- 工具推荐封面
- 带大表情主视觉的封面

### 2. 信息图 / 知识卡
内置比较成熟的卡片包括：
- 清单卡
- 对比卡
- 机制卡
- 产品地图
- QA 卡
- 流程卡
- 时间线卡

### 3. 一篇文章拆成一整套图片
这是它最强的场景之一。

适合：
- 飞书文章
- 公众号文章
- 长笔记
- 采访整理
- 产品更新
- AI 工具解读

### 4. 自由 SVG 创作
如果你不想被内置模板约束，可以直接让 agent 输出 `custom_svg`。

适合：
- 吉祥物
- 贴纸风图案
- 单页装饰插画
- 需要 agent 直接控制画面的页面

## 创意到底来自哪里？

这套技能不会凭空替你想出好创意。

更准确地说：
- 🧠 创意来自人类
- 🤖 视觉判断取决于 agent
- 🛠️ renderer 负责把这些决定稳定落图

这正是它的价值：
- agent 负责思考
- renderer 负责执行

如果 agent 判断很强，最终结果就会很强。
如果 agent 判断一般，这个技能也不会替它“脑补成神图”。

## Quick Start

### 快速做一张封面

```bash
python3 scripts/free_image_gen.py \
  --prompt "文字封面，标题 AI 产品设计原则，副标题 清晰层级 高识别度，主题：light，封面布局：hero_emoji_top，主视觉表情：💡" \
  --output /absolute/path/output/cover.png \
  --width 1080 \
  --height 1440
```

### 快速做一张信息图

```bash
python3 scripts/free_image_gen.py \
  --prompt "信息图 机制卡 角标：三个关键点 标题：AI Agent 为什么突然火了 副标题：不是模型更强了，而是入口和体验变了 1. 门槛更低 2. 分发更广 3. 商业化更真实" \
  --output /absolute/path/output/infographic.png \
  --width 1080 \
  --height 1440
```

### 给一篇文章，直接生成整套图片

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.md \
  --story-output-dir /absolute/path/output/article-story \
  --story-strategy auto \
  --width 1080 \
  --height 1440
```

这条命令适合快速打草稿。

### 最推荐：让 agent 先思考，再渲染

这是最能发挥这套技能能力的工作流。

让 agent：
- 读完整篇文章
- 决定怎么分页
- 判断哪页该保留文章结构
- 判断哪页该转成清单 / 机制卡 / 对比卡 / 地图 / QA 卡
- 保持内容忠于原文
- 先产出 `story-plan.json`
- 再调用 `free-imagegen` 渲染整套图片

这样最后会变成：
- agent 负责思考
- renderer 负责执行

## 默认输出行为

默认行为已经尽量收干净：
- 默认只输出 PNG
- 不会额外保存 SVG，除非显式加 `--keep-svg`
- 默认命名更整洁
- 默认输出目录也更清晰

## 自由度到底高不高？

这套技能不是“只能套模板”。

你可以：
- 用内置版式快速做封面和信息图
- 让 agent 规划整套图的分页和风格
- 直接让 agent 写 `custom_svg`

所以它的自由度来源不是“乱生成”，而是：
- 有结构时很稳
- 需要自由时也能放开

## fallback 和主路径怎么理解？

`illustration` 依然存在，但更适合当作 **轻量 fallback**。

适合 `illustration` 的场景：
- 快速抽象图
- 简单装饰图
- 轻量单图占位

更推荐优先使用 `custom_svg` 的场景：
- 具体对象
- 吉祥物
- 动物
- 机器人
- 贴纸风图案
- 需要 agent 直接控制视觉结果的页面

## 给 agent 的接入资料

如果你想接进 OpenClaw 或其他 agent 工作流，优先看这些：
- `references/story-plan.schema.json`
- `references/story-plan.template.json`
- `references/story-plan.guide.md`
- `references/story-plan.agent-prompt.md`
- `references/custom-svg-best-practices.md`
- `references/custom-svg.story-plan.sample.json`

这些文件的目标不是限制 agent，而是：
- 保留 agent 的自由判断
- 同时让输出结构足够稳

## 一句话总结

如果你要的是：
- 免费
- 纯本地
- 免 API
- 没硬件门槛
- 中文友好
- 小红书友好
- agent 可控
- 一篇文章直接变成一整套图

那 `Free ImageGen` 就是为这个场景做的。

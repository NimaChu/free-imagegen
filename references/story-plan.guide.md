# Story Plan Guide

Use this guide when an agent needs to turn a long article into a `story-plan.json` for `free-imagegen`.

This file is intentionally **not** a fixed recipe.

- `story-plan.schema.json` defines the data contract
- `story-plan.template.json` gives a minimum working skeleton
- this guide explains **how to judge pagination, layout, and style**

The goal is to keep judgment in the agent and keep rendering in the tool.

## Core Principle

Do not ask the renderer to decide the whole editorial structure.

The agent should decide:

- what the article is really trying to say
- where one page should end and the next should begin
- which parts should stay close to the original prose
- which parts are easier to understand as cards, lists, comparisons, or maps
- how much the whole set should feel unified
- whether the set should stay calm or become more playful

The renderer should only do this:

- place text cleanly
- keep images complete
- avoid overlap and bad wrapping
- execute the selected layout reliably
- render playful or restrained treatment only when the plan explicitly asks for it
- when given agent-authored SVG, preserve that SVG and only normalize canvas and export details

## Optional Expressiveness Controls

Use these only when they help the content.

- `tone`
  - `calm`: restrained, reading-first
  - `playful`: allows emoji badges, lighter stickers, and friendlier rhythm
  - `bold`: stronger contrast and punchier accents
  - `editorial`: more magazine-like and restrained
- `decor_level`
  - `none`: no extra decoration
  - `low`: a little extra texture
  - `medium`: visible playful treatment without turning the page into a poster
- `emoji_policy`
  - `none`: text only
  - `sparse`: one or two emoji accents when helpful
  - `expressive`: more visible emoji treatment

Use these controls to express intent, not to decorate everything by default.

Good uses:

- a summary page that should feel lighter and friendlier
- a tool roundup that benefits from a bit more energy
- an opening page aimed at social content rather than sober documentation

Bad uses:

- adding emoji to dense configuration notes
- making every page playful in a serious technical article
- using decoration to compensate for weak structure

## First Pass: Understand The Article

Before writing any cards, identify:

- the main claim
- the emotional hook
- the sections that carry the real value
- the parts that are explanation, evidence, steps, or conclusion
- whether the article already contains strong screenshots or illustrations

A good `story-plan` usually follows the article's real structure instead of flattening everything into one repeated card style.

## Voice Preservation

The output should express the article's content directly, not comment on the article from the outside.

Avoid meta phrasing like:

- "文章里提到"
- "作者认为"
- "文中指出"
- "这篇文章说"

Prefer direct expression:

- state the concept directly
- state the evidence directly
- state the conclusion directly

Only use meta wording if the page is explicitly about the author's framing or editorial method.

## Pagination Heuristics

Use page breaks when one of these happens:

- the article changes topic
- the article changes rhetorical job: explanation -> evidence -> example -> conclusion
- a paragraph group becomes too dense for one mobile page
- a screenshot or visual deserves its own page rhythm
- a section would read better as a card than as normal prose

Do not split only because a section is long. First ask whether the section should stay as an article page.

When a section is explanation-heavy and still reads smoothly as prose, prefer fewer pages with stronger structure over aggressively fragmenting it.

### Good page boundaries

- one page establishes the concept
- the next page lists the core capabilities
- one page explains the problem
- the next page shows the workflow or comparison
- one page gives the conclusion and action items

### Bad page boundaries

- splitting a natural paragraph in the middle just to force another layout
- turning every section into a card even when the original writing is already clear
- mixing two different rhetorical jobs on the same page if that makes the page unfocused

## Choosing A Page Type

### `article_page`

Use when the original writing itself is valuable and readable.

Best for:

- concept explanations
- narrative opening paragraphs
- nuanced argumentation
- pages that should feel like normal reading
- pages with one real screenshot plus a few intact paragraphs

Choose `article_page` when you want to preserve the article's voice.

### `article_note`

Use when the content is still prose-like, but contains configuration, code fields, CLI commands, URLs, or explanatory fragments that need a more structured note treatment.

Best for:

- config explanations
- field-by-field notes
- command snippets with surrounding explanation
- migration / setup warning pages

### `mechanism`

Use when the section explains a concept through several clear points.

Best for:

- 3-4 key traits
- core mechanisms
- why something matters
- structured explanation where each point is short

If the original text can be compressed into a few crisp statements, `mechanism` is usually better than leaving it as prose.

### `checklist`

Use when the page is really a summary, action list, takeaways, or pitfalls.

Best for:

- upgrade advice
- do / don't guidance
- pitfalls
- final conclusions
- closing pages

### `qa`

Use when the content naturally reads as questions and answers.

Best for:

- FAQ sections
- objection handling
- "why / what / how" structures

Do not force `qa` when the article is not actually asking questions.

### `comparison`

Use when the value comes from seeing before/after, old/new, manual/agent, or option A / option B side by side.

Best for:

- before vs after
- manual vs automated
- old workflow vs new workflow

Avoid it on phone-first pages when the content is too wordy to fit three columns cleanly.

### `flow`

Use when the reader needs sequence.

Best for:

- steps
- process explanation
- setup order
- automation pipelines

Do not use `flow` for large prose sections that are really explanation instead of sequence.

### `timeline`

Use when the content is genuinely chronological.

Best for:

- evolution over time
- historical milestones
- release sequence

If each point is too long, it probably should be `mechanism` or `article_page` instead.

### `catalog`

Use when the page is a compact scan of tools or products.

Best for:

- vendor lists
- tool roundups
- role-tagged products

If the products fall into clear layers, consider `map` instead.

### `map`

Use when the point is the relationship between groups, layers, or categories.

Best for:

- product landscapes
- ecosystem maps
- grouped tool categories
- role-based product overviews

`map` is usually better than `catalog` when the reader should first understand the structure of the space.

### `text_cover`

Use sparingly inside a story.

Best for:

- the auto-generated cover
- rare high-impact divider pages
- big editorial statement pages

Do not turn every section opener into a `text_cover` unless the article is intentionally poster-like.

### `custom_svg`

Use when the agent wants full control over the visual and does not want the renderer to choose a built-in layout.

Best for:

- free illustration
- mascots or characters
- specific recognizable objects such as cats, lobsters, tools, or robots
- decorative scene pages
- agent-authored diagrams that are easier to express directly in SVG
- any page where built-in templates would over-constrain the design

Provide one of:

- `svg_markup`: raw SVG string authored by the agent
- `svg_path`: absolute path to an existing SVG file

Use `custom_svg` when the page should be treated as a finished SVG composition, not as text that still needs layout decisions from the renderer.

For a concrete starting point, see:

- `references/custom-svg-best-practices.md`
- `references/custom-svg.story-plan.sample.json`

## Choosing `section_role`

Use `section_role` to describe the job of the page, not just its position.

### `cover`

Use for the main opening cover only.

### `chapter`

Use when the page starts a new conceptual section.

Typical signs:

- new topic
- new argument branch
- new section opener
- chapter-like page with more vertical breathing room

### `body`

Use for normal reading pages and most detail pages.

### `summary`

Use for conclusion pages, takeaways, next steps, or closing synthesis.

## Choosing `series_style`

### `loose`

Use when pages should feel more independent.

Good for:

- mixed-source content
- exploratory card sets
- pages that need noticeably different moods

### `unified`

Use when the whole set should feel like one editorial package.

Good for:

- article threads
- Xiaohongshu-style multi-page posts
- educational card sets

If unsure, `unified` is the safer default for article conversion.

For most article-to-image sets, prefer keeping the overall visual system consistent.

- default to one main theme family across the set
- only switch light/dark when there is a clear editorial reason
- if an inserted image feels semantically weak, omit it instead of forcing it
- if the set is `unified`, mixed themes should be a deliberate exception, not the default

## Common Failure Modes

- describing the article from the outside instead of expressing its ideas directly
- forcing every section into a built-in infographic template
- inserting unrelated images just because an image is available
- mixing light and dark pages accidentally inside a `unified` series
- overusing playful decoration on dense technical pages
- expecting the built-in `illustration` branch to behave like a fully open-ended drawing model
- using `illustration` for a specific recognizable object when the agent actually wants direct drawing control

If the page needs true free-form SVG illustration, use `custom_svg`.

## Common Failure Modes

Watch for these when writing a `story-plan.json`:

- the page talks about the article instead of expressing the article's idea
- the plan uses an image that is only loosely related to the page's message
- the set claims `series_style=unified` but flips light/dark repeatedly without a clear reason
- a summary page carries too much explanation instead of closing cleanly

If you see one of these, revise the plan before rendering.

## Choosing Theme And Density

### Theme

- `light`: best for prose, screenshots, article reading, and soft editorial pages
- `dark`: best for strong mechanism cards, summary cards, and high-contrast impact pages
- `auto`: only when the agent genuinely does not care

### Density

- `comfy`: article-like reading and lower-pressure pages
- `compact`: lists, summary cards, and denser infographics
- `auto`: acceptable fallback, but explicit is usually better

## Image Placement Guidance

Use `image_path` when a real image adds meaning.

Good uses:

- screenshots of a product being discussed
- charts or tables referenced in the text
- examples that anchor the explanation

Do not add an image just because a page feels empty.

If an image is weak, decorative, or unrelated, prefer a cleaner text page.

## Writing Better Bullets

When converting prose into bullet-based layouts:

- one bullet should express one idea
- keep each bullet scannable on a phone
- shorten filler language
- keep numbers, contrasts, and verbs
- prefer strong nouns and actions over long transitions

Bad:

- a long sentence with three different claims glued together

Better:

- one concise statement per bullet
- make the contrast or takeaway obvious

## A Practical Workflow

1. read the full article
2. outline the real sections in plain language
3. decide which sections stay prose and which become cards
4. decide page roles: `chapter`, `body`, `summary`
5. decide whether the full set should be `loose` or `unified`
6. write `story-plan.json`
7. render and inspect the result
8. revise only the pages that still feel wrong

## A Good Mental Model

Think of `story-plan.json` as:

- a content plan
- a layout plan
- a lightweight art-direction plan

It should tell the renderer **what each page is trying to do**, without forcing the agent into one fixed output formula.

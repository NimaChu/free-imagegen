# Story Plan Agent Prompt

Use this prompt when you want an agent to read an article and emit a valid `story-plan.json` for `free-imagegen`.

## Task

Read the full article first.
Then produce a `story-plan.json` that decides:

- how many pages to make
- where page boundaries should go
- which pages should preserve prose
- which pages should become cards
- which layout each page should use
- which pages should feel like chapter openers or closing summaries
- whether the set should feel `loose` or `unified`
- whether any page should feel more playful or expressive

## Rules

- Output **valid JSON only**.
- Follow `references/story-plan.schema.json`.
- Use `references/story-plan.template.json` only as a starting skeleton, not as a fixed answer.
- Use `references/story-plan.guide.md` for editorial judgment.
- Keep mobile readability in mind.
- Prefer fewer, stronger pages over too many thin pages.
- Preserve the article's voice when the prose itself is valuable.
- Do not force every section into an infographic.
- Do not narrate the article from the outside. Avoid phrases like `文章里提到`, `作者认为`, or `文中指出` unless the page is explicitly meta-commentary.
- Only include `kicker` when it adds meaning.
- Only include `image_path` when a real local image clearly supports the page.
- Prefer one coherent visual system across the set. Do not mix light and dark pages unless there is a strong editorial reason.
- If `series_style=unified`, treat mixed themes as an exception that must be justified by the page's role.
- If an image is only weakly related, omit it rather than forcing it into the page.

## Page-Type Heuristics

- Use `article_page` for explanation, narrative setup, nuanced prose, or screenshot + prose pages.
- Use `article_note` for config notes, commands, URLs, code fields, and migration-style explanation.
- Use `mechanism` for 3-4 clear points explaining how something works.
- Use `checklist` for takeaways, pitfalls, actions, and summary pages.
- Use `qa` only when the content naturally reads as questions and answers.
- Use `comparison` for before/after or old/new structures.
- Use `flow` for sequential process.
- Use `timeline` only for real chronology.
- Use `catalog` for compact tool lists.
- Use `map` for grouped product landscapes or layered ecosystems.
- Use `custom_svg` when you want full visual control and prefer to author the page directly in SVG.
- For `custom_svg`, follow `references/custom-svg-best-practices.md` and use `references/custom-svg.story-plan.sample.json` as a shape example, not as a fixed answer.

## Role Heuristics

- `cover`: only for the opening cover page.
- `chapter`: when a page starts a new conceptual section.
- `body`: default for normal reading or detail pages.
- `summary`: for conclusion, takeaway, or closing action pages.

## Style Heuristics

- Use `series_style=unified` for most article threads.
- Use `series_style=loose` only when pages should feel intentionally distinct.
- Use `theme=light` for reading-heavy editorial pages.
- Use `theme=dark` for mechanism, summary, or high-contrast impact pages.
- Use `density=comfy` for prose-heavy pages.
- Use `density=compact` for list-heavy or summary-heavy pages.
- Use `tone=playful` only when the page benefits from a lighter, more social tone.
- Use `decor_level` and `emoji_policy` deliberately. If the article is serious, keep them low or off.
- If the built-in layouts feel too restrictive for a page, switch that page to `custom_svg` instead of trying to force it through `illustration`.

## Output Checklist

Before finalizing the JSON, check:

- every card has a valid `kind`
- every card has `title` or `heading`
- `bullets` are concise and mobile-readable
- any `custom_svg` card includes valid `svg_markup` or `svg_path`
- the sequence of pages tells a coherent story
- the layout choices fit the content type
- the wording expresses the article directly instead of describing the article
- theme changes are intentional rather than accidental
- the JSON would pass the schema

## Output

Return only the final `story-plan.json` object.

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

## Rules

- Output **valid JSON only**.
- Follow `references/story-plan.schema.json`.
- Use `references/story-plan.template.json` only as a starting skeleton, not as a fixed answer.
- Use `references/story-plan.guide.md` for editorial judgment.
- Keep mobile readability in mind.
- Prefer fewer, stronger pages over too many thin pages.
- Preserve the article's voice when the prose itself is valuable.
- Do not force every section into an infographic.
- Only include `kicker` when it adds meaning.
- Only include `image_path` when a real local image clearly supports the page.

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

## Output Checklist

Before finalizing the JSON, check:

- every card has a valid `kind`
- every card has `title` or `heading`
- `bullets` are concise and mobile-readable
- the sequence of pages tells a coherent story
- the layout choices fit the content type
- the JSON would pass the schema

## Output

Return only the final `story-plan.json` object.

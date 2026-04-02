# Custom SVG Best Practices

Use `custom_svg` when the agent wants full control over a page and prefers to author SVG directly.

This mode is the best fit for:

- free illustration
- mascots and characters
- decorative opener pages
- hand-authored diagrams
- layouts that do not fit the built-in page types

## Principle

Let the agent decide the composition.

Let the renderer do only this:

- normalize canvas size
- preserve the SVG
- export a PNG reliably

Do not expect the renderer to rescue weak SVG composition.

## Recommended Canvas Habits

- Always assume the page will be rendered into the requested `width` and `height`.
- Keep important content inside a safe area.
- Leave breathing room near the edges.

Recommended safe area:

- left/right padding: `8%` to `12%`
- top padding: `8%` to `12%`
- bottom padding: `10%` to `16%`

If you place text too close to the bottom edge, it may feel cropped even when it technically fits.

## Text Rules

- Prefer short text inside `custom_svg`.
- Keep single lines well within the canvas width.
- If a line is long, break it intentionally instead of hoping it will still look good.
- Use `text-anchor=\"middle\"` only when the text block is truly centered in the composition.

Good:

- one short caption
- one label under an illustration
- one or two carefully composed title lines

Risky:

- paragraph-length text
- long subtitles with no manual line breaks
- oversized bottom captions

## Shape Rules

- Use simple geometry first: circles, rounded rectangles, paths, ellipses.
- Build the figure from a few large shapes before adding details.
- Prefer 3 to 6 dominant visual elements over 20 tiny details.

This tends to read better on mobile.

## Color Rules

- Use a limited palette.
- Choose one dominant fill color, one supporting accent, and one dark ink color.
- If the page has text, keep background contrast generous.

Simple palette pattern:

- background
- main subject
- accent
- dark detail color

## Mobile Readability

- Make the main subject large.
- Avoid many small labels.
- If the page must explain something dense, it probably should not be `custom_svg`.
- Use `custom_svg` for expressive pages, not for squeezing in lots of text.

## Good Use Cases

### Character Illustration

- cat
- robot
- mascot
- face or sticker-like object

### Decorative Scene

- abstract hero image
- chapter opener with a central illustration
- visual metaphor page

### Hand-Authored Diagram

- a simple concept drawing
- a relationship diagram where exact placement matters

## Bad Use Cases

- long article paragraphs
- dense checklists
- large comparison tables
- any page where the agent is trying to rebuild a built-in layout by hand for no reason

For those, prefer:

- `article_page`
- `mechanism`
- `checklist`
- `comparison`
- `flow`
- `map`

## Minimal Pattern

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1440">
  <rect width="1080" height="1440" fill="#FFF7EE"/>
  <circle cx="540" cy="620" r="220" fill="#F6B26B"/>
  <text
    x="540"
    y="1180"
    text-anchor="middle"
    font-family="PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif"
    font-size="80"
    font-weight="800"
    fill="#8A5B2C"
  >
    一句短标题
  </text>
</svg>
```

## Recommendation

When the user asks for a truly free-form illustration, prefer:

1. `kind: "custom_svg"`
2. agent-authored `svg_markup`
3. only minimal text
4. large central subject

That path is more reliable than trying to force the legacy `illustration` mode to behave like a fully open-ended drawing model.

# Game Assets

Visual asset library for the board, pieces, cards, and UI chrome — Rustic
Tabletop style (see the [UI Profile](catan-ui-directions.html) canvas from
Day 1-2). All files are plain, standalone `.svg` under
`frontend/src/assets/`, organized by category. Built ahead of Day 3-4 so the
board generator and later rendering days have real assets to work against
instead of placeholders.

---

## Read this before importing any of `pieces/` or `avatars/`

Those files use `fill="currentColor"` so one shape can be reused across all
player colors instead of pre-baking 6 color variants per piece. **This only
works if the SVG is inlined into the DOM** (e.g. imported as a React
component via `vite-plugin-svgr`, or inlined with `dangerouslySetInnerHTML`).

A plain `<img src="settlement.svg">` does **not** inherit CSS `color` —
browsers render externally-referenced SVGs in an isolated image context.
Confirmed by hand: rendering these via `<img>` produced solid black shapes
regardless of the wrapping element's color.

If inlining isn't convenient at a given call site, the alternative that does
work with a plain file reference is a CSS mask:

```css
.piece {
  background-color: var(--player-color); /* e.g. oklch(52% 0.16 35) */
  mask-image: url("/src/assets/pieces/settlement.svg");
  mask-size: contain;
  mask-repeat: no-repeat;
  -webkit-mask-image: url("/src/assets/pieces/settlement.svg");
  -webkit-mask-size: contain;
  -webkit-mask-repeat: no-repeat;
}
```

Both techniques were verified rendering correctly before this was committed.

---

## Player color palette

Not pre-baked into any asset — apply via inlining or `mask-image` per piece,
per player. Matches classic Catan colors, adapted to the project's oklch
token system:

| Player | Color |
|---|---|
| Red | `oklch(52% 0.16 35)` (same hue as the brick resource / primary UI accent) |
| Blue | `oklch(50% 0.14 250)` |
| Orange | `oklch(65% 0.15 55)` |
| Cream/White | `oklch(92% 0.01 85)` — needs a dark border/outline when used on the parchment background, or it disappears |
| Green (5-6p only) | `oklch(50% 0.13 155)` |
| Brown (5-6p only) | `oklch(38% 0.07 50)` |

## Inventory

### `resources/` — resource cards
`card-back.svg` (shared back) + `wood.svg`, `brick.svg`, `sheep.svg`,
`wheat.svg`, `ore.svg`. 120×168 viewBox (standard card ratio). Each front
uses a resource-colored top panel with a cream icon silhouette, corner pips,
and a name label.

### `tiles/` — board hexes
`forest.svg` (wood), `hills.svg` (brick), `pasture.svg` (sheep),
`fields.svg` (wheat), `mountains.svg` (ore), `desert.svg`, plus
`border-water.svg` for the ocean frame around the playable board. 200×200
viewBox, pointy-top hexagon (matches the axial hex-grid orientation the Day
3-4 board generator will use). Reuses the same icon glyphs as the resource
cards for visual consistency between hand and board.

### `ports/` — harbors
`generic.svg` (3:1, any resource) + `wood.svg`, `brick.svg`, `sheep.svg`,
`wheat.svg`, `ore.svg` (2:1, resource-specific). 64×64 viewBox. One asset
per port *type* — the board places multiple copies of `generic.svg` at
different locations, not multiple distinct files.

### `pieces/` — player pieces (see the currentColor note above)
`settlement.svg`, `city.svg`, `road.svg` (all `currentColor`, recolor per
player) + `robber.svg` (fixed dark fill — the robber is neutral, never
player-colored, per the rules).

### `avatars/`
`default.svg` — a generic silhouette, `currentColor`, for a player who
hasn't set anything else. Same recoloring caveat applies.

### `dice/`
`die-1.svg` through `die-6.svg`, 64×64, standard pip layouts.

### `dev-cards/`
`card-back.svg` (shared, purple, distinct from the resource-card back so
the two decks are never visually confused) + `knight.svg`,
`victory-point.svg`, `road-building.svg`, `year-of-plenty.svg`,
`monopoly.svg`. Same 120×168 card shape as resource cards but a uniform
dev-card purple panel (`oklch(50% 0.12 300)`) — this is a new token, not
previously in the UI profile — differentiated by icon and label rather than
by color per sub-type.

### `badges/`
`longest-road.svg`, `largest-army.svg` — circular medals, both stamped
"+2 VP". 140×170 viewBox.

### `icons/`
`logo.svg` (the brand mark, fixed brick/wheat colors — not
`currentColor`, since it's a fixed mark, not a recolorable one) plus
stroke-based UI action icons: `trade.svg`, `accept.svg`, `deny.svg`,
`counter.svg` (propose a counter-offer), `settings.svg`, `logout.svg`,
`close.svg`, `chevron.svg` (down — rotate via CSS for other directions
rather than shipping 4 files).

---

## What's deliberately not here

- **Number tokens** (the 2-12 discs on each hex) aren't a static asset —
  they're simple enough (a circle + text) to draw directly in code, as
  already done in the Day 1-2 game-screen mockup.
- **Per-player-color pre-rendered pieces** (e.g. `settlement-red.svg`) —
  deliberately avoided in favor of one neutral shape recolored at render
  time. Revisit only if the mask/inline approach proves impractical once
  real rendering code is written.
- Anything not listed above that comes up later (trade-history icons, a
  win/trophy screen, etc.) — add it here when it's actually needed rather
  than guessing scope now.

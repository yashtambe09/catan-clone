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
`forest.png` (wood), `hills.png` (brick), `pasture.png` (sheep),
`fields.png` (wheat), `mountains.png` (ore), `desert.png` — **swapped from
the original flat SVGs (Days 17-25) to the painterly "Settlers Kit" PNG
pack** (`settlerstiles.zip`, part of [Settlers
Kit](https://opengameart.org/content/settlers-kit) by Rainbow Design,
licensed **CC-BY-SA 3.0 / GPL 3.0 / GPL 2.0**, attribution optional per the
author but credited here anyway). 219×256px RGBA, pointy-top hexagon —
verified the aspect ratio matches the true hex bounding box almost exactly
(no viewBox-scaling constant needed; rendered at
`HEX_SIZE*sqrt(3)` × `HEX_SIZE*2` directly). `border-water.svg` (the
original flat-SVG ocean frame) is unused and kept as-is — not part of this
swap.

Deliberately **not** swapped: ports, pieces, resource cards, dev cards, and
all UI chrome stay on the original flat-vector system — this pack only
covers terrain tiles and number tokens (see below), and the rest of the UI
would clash if it half-matched a different asset's painterly style.

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

## `numbers/` — number tokens

`2.png` through `12.png` (no `7` — never appears on a hex), from the same
**Settlers Kit** pack/license as `tiles/` above (`numbers2.zip`). 70×70px
RGBA, parchment disc with the number baked in. **Originally** drawn
directly in code (a plain `<circle>` + `<text>`, as noted below in the
project's early history) — swapped to this pack alongside the tiles.

One gap versus the original: the pack colors every digit the same
maroon, unlike the physical game's convention (and this project's
original code) of showing 6/8 in red as a "hot number" cue. Preserved
that distinction with a thin accent-colored ring drawn in code around
hot-number tokens, rather than losing the cue entirely.

## What's deliberately not here

- **Per-player-color pre-rendered pieces** (e.g. `settlement-red.svg`) —
  deliberately avoided in favor of one neutral shape recolored at render
  time. Revisit only if the mask/inline approach proves impractical once
  real rendering code is written.
- Anything not listed above that comes up later (trade-history icons, a
  win/trophy screen, etc.) — add it here when it's actually needed rather
  than guessing scope now.

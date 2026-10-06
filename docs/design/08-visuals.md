# 08. Visuals

## The viewer reads a log (proposed)

The game has no renderer inside the engine. A **viewer** reads a run log and
draws it: the map, the personas, their actions, their words. Any run, local
or hosted, replays the same way, and a replay is a file one can share.

- **Web viewer** first: a static page (TypeScript, a canvas), the log loaded
  from disk or a URL. Works offline, opens on a phone, can be published as
  a page.
- **Terminal viewer** later, if wanted: the same log drawn in cells, in the
  style of avatar7's panes.

## Screen (proposed)

- **The map** in the middle, tiles and personas on them.
- **A timeline** under it: day, hour, season; play, pause, step, scrub.
- **A side panel** for the selected persona: needs, inventory, its last
  decision and the reason it gave, what it wrote to memory.
- **Speech** as short bubbles over the map; the full exchange in the panel.
- **Moods** (05-personas.md) as a tint or a small mark on the sprite, and
  named in the panel: at most two at a time.
- **The score** as three bars (Goal, Life, Together) that move during the
  replay.

## Art direction (open: one axis to choose)

Three directions, each coherent with the flux7 aesthetics:

| Direction | The world looks like | Fits |
| --- | --- | --- |
| **Comptoir** (trading post, sea charts) | an engraved map, botanical plates, rattan and brass frames, ink and paper tones | farming, trade, a small settlement: the closest to the game's content |
| **Belle Époque future** | Art nouveau curves, brass instruments, a Verne-like expedition journal | the "arrive with nothing" story, the chronicle of a colony |
| **Cyber 1995** | a neon grid, CRT scanlines, terminal glyphs | the agents-and-governance reading; the shortest path from avatar7 |

The Comptoir direction reads as the most natural for a world of crops,
barter and a river to cross; to decide.

## Assets (proposed)

- **Tiles**: a small set (around 20) in one consistent style, made with
  flux7-studio, cut to a grid; seasons as palette shifts, not new tiles.
- **Personas**: a portrait each, from the persona file's `portrait` or a
  default per character; a tiny sprite on the map (16 or 24 px).
- **Icons** for actions and resources, the same style as the tiles.

## Open

- Top-down or slight isometric? Top-down is simpler and reads better for
  a log; isometric is warmer.
- Pixel art or illustrated (engraving)? Pixel art scales to many tiles
  cheaply; engraving fits the Comptoir direction.

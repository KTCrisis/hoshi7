# flux7-hoshi: design

The foundations of each part of the game, written before the first line of
engine code. Each page says what is **decided**, what is **proposed** (to
confirm or change), and what is **open**.

| Page | Part |
| --- | --- |
| [01-vision.md](01-vision.md) | what the game is, for whom, what makes it different |
| [02-gameplay.md](02-gameplay.md) | the player's loop and the personas' loop |
| [03-world.md](03-world.md) | the world: map, time, needs, resources, recipes, goals |
| [04-rules.md](04-rules.md) | rules as data: YAML recipes, CEL conditions |
| [05-personas.md](05-personas.md) | what a persona is, what it carries over, the persona file |
| [06-architecture.md](06-architecture.md) | engine, runner, models, MCP, mesh7 and mem7, the four seams |
| [07-scoring.md](07-scoring.md) | what "the best persona" means, and fairness |
| [08-visuals.md](08-visuals.md) | the viewer, the art direction, the assets |
| [09-animation-audio.md](09-animation-audio.md) | replay, motion, day and seasons, sound and voices |
| [10-roadmap.md](10-roadmap.md) | from a vertical slice to a hosted arena |

## Decided so far (4 October 2026)

- A game others can download and play, with their own model at first
  (Ollama by default, an API key optionally); later, hosted on servers with
  stronger models.
- The player's game may be designing the best persona.
- Personas act through tools; their memory goes through flux7-memory.

Everything else in these pages is a proposal.

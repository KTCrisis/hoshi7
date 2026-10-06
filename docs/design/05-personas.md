# 05. Personas

## A persona is a file, not a program (proposed)

```yaml
name: Mirai
version: 3
character: >
  A patient farmer who trusts slowly. Speaks little, keeps promises.
priorities:            # read by the persona's prompt, not by the engine
  - keep everyone fed through winter
  - never trade away the last tool
memory:
  keep: [trades, promises, who_lied, where_resources_are]
  forget_after_runs: 5
  budget: { recall_items: 8, write_per_day: 4 }
voice: { tone: dry, length: short }
portrait: mirai.png    # optional, see 08-visuals.md
```

The engine builds the persona's prompt from this file, the same way for
every persona; a player cannot inject instructions into the engine's
framing. What differs between personas is only what the file says.

## What a persona carries over (proposed)

- Between runs, its memory in flux7-memory, under its own scope (mem7's
  per-agent scopes), with provenance: which run, which hour, what it saw.
- The persona file decides what it keeps (`memory.keep`) and how much it
  may recall per hour (`budget`): memory strategy is part of the craft.
- A fresh persona starts empty; a persona's memory can be reset by the
  player.

## Moods (proposed): states, derived, never decreed

A persona in a world has moods that come from its needs, its relations and
the common goal, not from a single event. The engine derives them from the
log; a persona cannot decide to feel trusting.

| Source | Moods | Derived from |
| --- | --- | --- |
| Needs | hungry, exhausted, cold | a gauge under its threshold |
| Relations | trusting, wary, grateful, hurt | promises kept or broken, help received, the last hours of the log |
| Goal | hopeful, resigned | the goal's progress against the time left |
| Rest | calm | none of the above |

Three rules keep them legible:

- **Computed, not chosen**: the engine derives them; no action sets one.
- **They feed the prompt and the viewer, not the rules**: the persona knows
  how it feels and the viewer tints its sprite, but what is allowed does not
  change, so the engine stays deterministic.
- **One or two at a time**, shown in the panel, so a spectator reads why a
  persona betrayed: it was hungry and wary.

avatar7's five moods (idle, watch, deny, error, wait) are reactions to a
session's events; these are states of a life. A persona that exists in both
projects could show hoshi's states with avatar7's faces.

## Reference personas (proposed)

A small cast shipped with the game, so a player's persona always has
company: a hoarder, a helper, a trader, a liar, a wanderer. They double as
the baseline scores (07-scoring.md). Some may come from avatar7's cast
(their characters, not their faces), which links the two projects.

## Open

- Can a persona see the score during a run? (Probably not: it plays the
  world, not the metric.)
- Is the persona's prompt template visible to players? Visible is fairer
  and easier to learn; hidden protects against gaming it.
- Memory shared between personas (a common chronicle) as a world feature?

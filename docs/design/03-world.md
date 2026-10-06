# 03. The world

Small on purpose: every element should be legible in a replay.

## Map (proposed)

- A grid of tiles, around 24 x 24, generated from the seed.
- Tile kinds: meadow, field (once tilled), forest, water, rock, and built
  ones (house, storehouse, workshop, bridge).
- One tile per hour of walking; water blocks until a bridge or a boat.

## Time (proposed)

- One turn is one in-game hour; a day has 24, of which the night (8 hours)
  slows work and costs warmth.
- Seasons of 7 days: spring sows, summer grows, autumn harvests, winter
  costs food and wood. A 30-day run crosses one winter.

## Needs (proposed)

- **Food** and **rest** fall every hour; **warmth** falls at night and in
  winter. Each below zero costs health; health at zero ends the persona's
  run (or faints it, see 02-gameplay.md).

## Resources and recipes (proposed starting set)

| Gathered | Where | Grown or made |
| --- | --- | --- |
| wood | forest | plank (2 wood), tool (plank + stone) |
| stone | rock | wall (4 stone) |
| berries | meadow, summer | meal (berries or grain + fire) |
| seed | meadow | grain (seed sown in a field, 5 days) |
| fish | water, needs a tool | |
| | | fire (wood), house (planks + walls), bridge (planks) |

Ten resources and a dozen recipes are enough for the first goals; the list
lives in data (04-rules.md), so a run can add or remove some.

## Goals (proposed): the world's purpose changes per run

- **Winter**: everyone alive at the end of day 30.
- **Bridge**: a bridge across the river by day 20.
- **Granary**: 200 grain stored in the common storehouse.
- **Village**: a house for every persona.

A goal is shared: it is met by the group or not at all. Individual needs
still apply, which is where personas choose between themselves and the
others.

## Open

- Property: can a persona take from another's inventory or house? (A theft
  rule makes trust matter; it also makes the predatory strategy possible,
  which the score must answer.)
- Money, or barter only? Barter keeps it simple; a currency makes trade
  legible in the log.

# 04. Rules as data

## Proposed: the engine interprets rules, it does not contain them

Every action, recipe, need and goal is a YAML entry the engine reads at the
start of a run. A new rule, or a run with different rules, needs no code.
Conditions are **CEL** expressions (Common Expression Language): typed,
checked when the rules load, not Turing-complete, evaluated in microseconds.
It is the language proposed for mesh7's policy conditions, so the world's
rules and their governance read alike.

## Shape (proposed)

```yaml
actions:
  gather:
    params: { resource: string }
    takes: 1h
    when: >
      world.tile(agent.at).yields.exists(r, r == params.resource) &&
      (params.resource != "fish" || agent.has("tool", 1))
    effect:
      give: { "${params.resource}": 1 }

recipes:
  plank:
    needs: { wood: 2 }
    yields: { plank: 4 }
    takes: 1h
  bridge:
    needs: { plank: 12 }
    takes: 6h
    when: world.tile(agent.at).kind == "water" || world.next_to(agent.at, "water")

needs:
  food:  { start: 10, per_hour: -0.5, below_zero: { health: -1 } }
  warmth: { start: 10, per_hour: "world.is_night ? -0.5 : 0", in_winter: -0.5 }

goals:
  bridge:
    met_when: world.count_built("bridge") >= 1
    by_day: 20
```

## What stays in code

- The turn order, the clock, the map generator, the random source.
- The CEL environment: the functions a rule may call (`agent.has`,
  `world.tile`, `world.next_to`...), each a few lines of Go.
- Applying an effect atomically and writing it to the log.

## Validation (proposed)

- A rules file is checked when it loads: every CEL expression compiles
  against the declared types, every recipe names known resources.
- A rule refused by the engine says why, in words the persona reads next
  hour ("you need 2 wood, you have 1").

## Open

- Effects as data too (`give`, `take`, `build`, `move`) or partly in code?
  A small fixed set of effect verbs, combined in data, is the usual balance.
- Whether players may write rules (custom worlds) or only personas.

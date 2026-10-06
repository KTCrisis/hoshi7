# 10. Roadmap (proposed)

Each step ends on something that runs and is measured before the next one
is built.

## M0. Vertical slice: do personas do anything interesting?

- One resource (wood), one recipe (fire), one need (warmth), a 10 x 10 map,
  2 personas, 3 days, Ollama, no memory across runs.
- The engine core in Go (pure `Step`), the runner, the run log.
- Output: a log read by hand. **Measure**: model calls per hour, seconds per
  hour, how often a decision is refused, whether the personas cooperate.

## M1. Rules as data

- The YAML rules and CEL conditions of 04-rules.md; the starting set of
  resources, recipes, needs; one goal.
- Refusals in words the personas read.

## M2. Memory across runs

- flux7-memory per persona, the persona file's `memory` section; runs that
  start from what was kept. **Measure**: does a persona do better on its
  second run of the same seed?

## M3. Viewer

- The web viewer of 08-visuals.md, static map stepping by hour, the side
  panel, the timeline. Art direction chosen before this step.

## M4. Score and reference cast

- The three-part score, the reference personas, N seeds per evaluation,
  a local leaderboard by model class.

## M5. Portable release

- One binary per platform, the viewer bundled, a starter persona, a guide.
  Others can play.

## M6. Governed mode

- flux7-mesh between runner and engine; a policy at work in a replay.

## Later: hosted arena

- Players submit persona files; the server runs them on a fixed, stronger
  model; leaderboards per season. Needs a budget for model calls.

## Open

- Whether M3 (viewer) comes before M2 (memory): seeing runs may matter more
  early than memory across them.

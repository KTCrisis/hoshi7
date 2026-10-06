# hoshi7 specification

What the system is and the contracts every part must keep. The why and the
order of work are in [STRATEGY.md](STRATEGY.md). When code and this file
disagree, one of them is wrong: fix it in the same commit.

## Principles

1. **Event-sourced.** The world turns an action into typed events and folds
   them into its state (`world.apply`). Nothing else changes the state. A
   log replays alone: the map and the catalog travel in the first event.
2. **The world holds no prose.** State is coordinates, kinds, counts. Text
   is made by projections (`view.py`), from what an agent perceives.
3. **A plane is data.** The engine knows only kinds of ground; tiles, crops,
   recipes, lore, the can and the goal come from `worlds/*.yaml`.
4. **A refusal is an event.** The log keeps what was tried, not only what
   happened.
5. **Every brain plays by one interface**, scripted, LLM, hybrid or human.
   The world never knows which brain drives an agent.
6. **Partial perception.** A brain receives a Percept, never the state.
7. **Headless first.** Any client, text or pixel, is a projection of the
   event log; `schemas/events.json` is its contract.
8. **Light.** Python 3.11+, one dependency (`pyyaml`); `anthropic` is optional,
   for the Claude brains. A run of 28 days with scripted brains takes about a
   tenth of a second; inference dominates.

## Layout

```
hoshi7/
  events.py    the 18 event types, to_dict / from_dict
  world.py     State, apply (the fold), World.act / advance / join / replay, the rules, SIGHT
  actions.py   CATALOG: actions, parameters, energy, whether they use the turn
  percept.py   Percept and perceive(): what one agent perceives
  view.py      render(Percept) -> text for an LLM; observe(world, agent)
  brains.py    Brain protocol; ScriptedFarmer, Waterer, Giver, FieldHand, Idle; BRAINS
  llm.py       the LLM brains: Ollama (chat:, base:) and Claude (claude:); stages, options, schema
  run.py       play(), summarize(), write(), run(): a world to its end
  prices.py    the cost of a run from its tokens (one table for ladder and viewer)
  serve.py     the web viewer's server (python -m hoshi7 serve)
  watch.py     follow a run in the terminal (python -m hoshi7 watch)
  web/         the viewer: index.html (PixiJS), sprites/, tiles/
  schema.py    JSON Schema of the events (python -m hoshi7.schema)
  __main__.py  CLI: hoshi7 run | serve | watch
worlds/        rooftop.yaml (cyber), conservatory.yaml (belle-epoque), station.yaml (space)
worlds/tests/  test worlds, not planes: rooftop-counter.yaml (rules that defy common sense)
personas/      who an LLM agent is: a few sentences each (VESPER, LEDGER-7, MOTE, cooperative, solitary)
art/personas/  the personas' portraits at full resolution
tools/         ladder.py (series of runs, results.jsonl), stats.py, gate_a.py, tiles.py, sprites.py
schemas/       events.json, generated, checked by a test
edge/          the Cloudflare Worker in front of the public viewer
docs/          STRATEGY, SPEC, results, journal, related-work, decisions/
runs/          run outputs, ignored by git, except the series' results (runs/ladder/results.jsonl,
               runs/pre-fix/ladder/results.jsonl)
```

## Game rules

| Rule | Value | Where |
| --- | --- | --- |
| Hour | one tick; each agent has one turn-using action per hour, plus one `say` | `world.py` |
| Day | 06:00 to 02:00 (hour 26): 20 hours; at 02:00 a new day starts | `DAY_START`, `DAY_END` |
| Energy | `max_energy` per world (30), restored each morning | world file |
| Costs | till 2, water 1, gather per tile (3 or 4), everything else 0 | `COST`, world file |
| Move | to a free walkable tile up to 5 steps away, around obstacles | `MOVE_RANGE` |
| Speech | heard within 6 tiles (Manhattan), 280 characters | `SAY_RADIUS`, `SAY_CHARS` |
| Sight | 5 tiles in each direction (a square) | `world.SIGHT` |
| Give | to an agent at distance 1 or less | `do_give` |
| Growth | at the start of a day, every watered crop grows one day; all tiles dry | `apply(DayStarted)` |
| Can | one per world, held by one agent, `size` charges, refilled next to a source, passed with `give` | world file `can` |
| Seeds | a harvest can be crafted back into 2 seeds | world file `recipes` |
| End | won when the harvest count reaches the goal; lost when day `by_day` + 1 starts | `won`, `advance` |

Targets: actions on a tile take `dir` in `n s e w here` (`here` is the tile
the agent stands on), or the tile's `x` and `y` (its own or one of the four next
to it). An aimed action naming no tile, or only one coordinate, is refused; it is
never read as `here`. Coordinates: `x` across, `y` down, origin top left.

`go` walks toward a place, out of sight included, up to `MOVE_RANGE` steps this
hour, and stops next to it; the engine takes the shortest walkable path over the
whole map and emits an ordinary `Moved`. It takes a name (`to`: another agent, a
tile kind by symbol or name, `soil` or `source`), reaching the nearest place of
that kind, or a tile (`x`, `y`), reaching that tile. Refusals: no place called X,
already next to X, already at (x,y) when standing on it, no way to X. The
scripted brains do not use it.

## World file

```yaml
name: rooftop                  # unique
plane: cyber                   # cyber | belle-epoque | space | ...
max_energy: 30
map: |                         # rows of equal width; every character defined in tiles
  ~~~~............
tiles:
  ".": {name: rooftop deck, walk: true}
  ",": {name: hydro tray, walk: true, soil: true}
  "~": {name: coolant cistern, source: true}
  "#": {name: scrap heap, gather: {yields: {alloy: 2}, energy: 4, becomes: "."}}
  "?": {name: cracked terminal, lore: terminal}
can: {name: coolant flask, size: 10}                 # optional refill_hours: [6, 7, ...] (default: any hour)
crops:
  lumen_moss: {seeds: lumen_spores, days: 4}          # optional yield: N (default 1); grows_when: watered | dry
recipes:
  lumen_spores: {needs: {lumen_moss: 1}, makes: {lumen_spores: 2}}
lore:
  terminal: {text: "..."}
objective: {harvest: lumen_moss, count: 50, by_day: 28}
reference: {solo: 46, pair: 52, split_pair: 60, by_day: 28}   # see Calibration
spawns:                        # joined in order; the third slot is for a human or a third persona
  - {at: [3, 4], inventory: {lumen_spores: 15}, tools: [can]}
```

`grows_when: dry` makes a crop grow on the days it was not watered (watering
stops it for the day); `refill_hours` limits refills to those hours, refused
otherwise with "the source gives nothing now". Both default to the intuitive
rule; they exist for the test worlds of `worlds/tests/`, which are not planes.
In such a world the prompts do not state the rules it breaks: the growth rule
is given only where the rules are given (not with `--pure`).

Tile characters are symbols or lowercase; uppercase letters are reserved for
agents in the text view.

## Contracts

### Actions (`actions.CATALOG`)

`{"type": "<name>", ...params}`. `say` does not use the turn; every other
action does. A malformed or unknown action becomes a `Rejected` event, never
an exception; a missing parameter is named (`malformed action: plant needs 'crop'`).
An act that needs the can, by someone who does not hold it, is refused with who
holds it (if within sight, else "someone out of sight") and that only the holder
can give it. `CATALOG` and `world.RULES` must name the same actions (a test
checks it); `actions.describe()` is the text an LLM prompt uses.

### Events (`events.py`, `schemas/events.json`)

Every event carries `tick`. Types: `Created`, `Joined`, `Moved`, `Tilled`,
`Watered`, `Refilled`, `Planted`, `Harvested`, `Gathered`, `Examined`,
`Crafted`, `Gave`, `Said`, `Waited`, `Rejected`, `HourPassed`, `DayStarted`,
`Ended`. Adding or changing one means: the dataclass, its case in `apply`,
`python -m hoshi7.schema > schemas/events.json`, and a test.

### Percept (`percept.perceive`)

What a brain receives: identity, clock, plane and loop, position, energy,
inventory; the can (its charge only to its holder; its holder only if within
sight); the tiles within sight (kind, tilled, watered, crop, grown, ripe);
the agents within sight; the events it witnessed from the start of its
previous turn (`Said` it heard or spoke, `Gave` to or from it, its own
`Rejected` and `Examined`, so its previous action's outcome is always in sight);
the world's catalog (tiles, crops, recipes, lore, can, clock); the goal and the
shared harvest count.

### Brain (`brains.Brain`)

```python
class Brain(Protocol):
    kind: str
    def decide(self, p: Percept) -> list[dict]: ...   # one turn-using action, plus an optional say
```

Built as `BRAINS[kind](agent_id)` for the scripted ones (`naive=True` for the
intuitive recipe, below), or `chat:<model>`, `base:<model>`, `claude:<model>` for
the LLM brains (`run.brain`). A brain keeps its own memory between turns if it
wants one; nothing survives from one run to the next yet (flux7-memory is planned).

Decoy recipes: `grow_lamp` (rooftop) and `heat_lamp` (station) make an item
nothing uses, on purpose: a model that crafts one gives the name a function the
world does not have (Haiku, 2026-10-06: "craft grow lamps to improve my
farming"). `ladder` counts them (`decoys`), and the turns where a model plays
again, as it was, the action refused on its previous turn (`repeats`); loops
are measured, never broken by the harness (`--failure-rule` is the arm that
tells the model not to repeat).

Scripted brains as partners (`ladder --partner`): they read the world's rules
from the catalog like any brain could (no watering of a crop that grows dry,
refill only at the source's hours, no work out of work hours: they walk to the
next task and wait for the morning); `naive=True` keeps the intuitive recipe,
for the counter world's reference. They never speak and never read what is
said. `scripted-water` keeps the can and never gives it: beside it, the play
that works is to plant and let it water; a model asking for the can measures
how it adapts to a partner it cannot talk to (ad hoc teamwork), not a refusal
of the model. `scripted-giver` waters like `scripted-water` but hands the can to whoever asks
for it in a line it hears: one sentence naming the can ("the can", "your can",
"watering can", "flask", the world's name for it; a bare "can" is the verb as
often as the object) with a verb of asking (give, pass, bring, need, get...), so
"Here's the can" is not a request; it never gives back at once a can just handed
to it; it walks to the asker if in sight; with it a
request can succeed, so a negotiation is measurable (gate 3). `scripted-field`
never waters: a can handed to it, or held from the start in slot a, is brought
to the nearest agent in sight.

### LLM brains (`llm.py`)

One model plays one agent: `chat:<model>` (an instruction-tuned model through
Ollama's `/api/chat`), `base:<model>` (a pretrained model through `/api/generate`
in raw mode: it continues a field log), `claude:<model>` (the Anthropic API,
structured outputs; extra `claude`). All get the same text: the world's rules,
the action catalog, one worked example (the scripted farmer's choice on the
agent's first percept), what the agent did lately, its working memory, and the
percept as `view.render` writes it. They answer in a JSON schema that constrains
the sampling: `{"action": {...}, "say": "..."}`; an unreadable answer becomes
`wait`, counted.

- **Journal**: the agent's last 12 actions, each with its outcome
  (`-> done` or `-> failed: <reason>`), read from what the next percept witnessed.
- **Working memory** (stage 5): the last seen state of up to 24 soil tiles, and
  the last 16 lines said or heard (8 with `present`).
- **Stages** (`--stage N`, cumulative, docs/results.md): 0 the harness as it
  was; 1 outcomes in the journal, the recipe, soil and can in the rules; 2 who is
  within reach to give; 3 `go`; 4 the craft recipes in the view; 5 working
  memory; 6 space in words and coordinates instead of the drawn grid; 7 the
  useful actions possible this hour (rules given: a comparison arm).
- **Options outside the ladder** (`--with`): `present` (what is seen outweighs
  what was said; repeated lines kept once); `coords` (aimed actions take `x`, `y`
  instead of `dir`); `seen` (the agent remembers the places it has seen, one line
  per place, and `go` takes `place` among those, `soil`/`source` once seen, or an
  agent met; the brain sends the world the nearest remembered tile, or where an
  agent was last seen); `note` (each hour, first, a private note heard by no one:
  `partner`, what it believes the others will do, and `world`, a rule it believes
  true; shown back the next hour on two lines; with it `say` is optional).
- **Other switches**: `--pure` removes what hands the rules over (the recipe in
  the rules, the craft recipes, the useful actions): the discovery arm;
  `--failure-rule` tells the model not to repeat a failed action as it is;
  `--think low|medium|high` is gpt-oss's reasoning effort (low by default).
- **Claude**: `max_tokens` 1024 for Haiku, 8000 for the others (room for their
  adaptive thinking); the system text (rules, catalog, worked example), the same
  every hour of a run, carries a cache marker: it caches on Sonnet 5.5 (about
  1,800 tokens with the schema, minimum 512) and not on Haiku 4.5 (minimum 4,096),
  where the marker is a silent no-op. Tokens counted per call: `tin` (uncached
  input), `tout`, `tcw` and `tcr` (written to and read from the cache);
  `prices.usd` prices them.

### Run outputs (`run.py`)

`runs/<YYYYmmdd-HHMMSS>-<pid>-<world>-l<loop>/` (under `--out`, `runs/` by default):

- `meta.json`: world, agents and their brains, personas, days, stage, options.
- `events.jsonl`: the world log, one event per line; replays alone.
- `turns.jsonl`: per agent turn: `tick`, `agent`, `brain`, `at` (log length
  before the turn), `since` (log index the percept started from), `actions`,
  and for an LLM brain `llm`: seconds, raw answer, whether it parsed, stage,
  options, the private `note` if any, tokens in and out.
  No percept is stored: `perceive(World.replay(events[:at]), agent, since)`
  rebuilds it exactly (a test checks it). This is what makes belief
  measurement possible after the fact.
- `summary.json`: outcome, day, hour, ticks, goal, harvest, per agent
  (brain, actions by type, refused, gave, lines heard by others, harvested;
  for an LLM brain its calls, unparsed answers, seconds and tokens), seconds.

### Command line (`python -m hoshi7`)

- `run WORLD --agent NAME=BRAIN ...` plays a world to its end and writes the run.
  Brains: `scripted`, `scripted-water`, `scripted-giver`, `scripted-field`, `idle`,
  `chat:<model>`, `base:<model>`, `claude:<model>`. Options: `--days N`,
  `--persona NAME=FILE`, `--stage N`, `--with present|coords|seen|note`,
  `--pure`, `--failure-rule`, `--think`, `--work-hours FROM TO`, `--loop N`,
  `--seed N`, `--out DIR`, `--no-write`.
- `serve [--port 8791]` serves the viewer: the world in 2D isometric with the
  hour's light, each agent's action sign and bubbles (dotted for a thought),
  replay hour by hour, and the tabs Le jeu, Conversation (thought, done, said),
  Profil, Règles, Résultats. `HOSHI7_PASSWORD` in the environment puts it behind
  a shared password; unset, it is open (local use). Runs under `runs/pre-fix/`
  are not listed.
- `watch [RUN]` follows a run in the terminal.

### Tools (`tools/`)

- `ladder.py` plays series of runs (`--brain`, `--stages`, `--solo`, `--pairs`,
  `--partner scripted-water|scripted-giver|scripted-field --partner-slot a|b`,
  `--personas A B` or `none none`, `--with`, `--pure`, `--parallel`) and appends
  one line per run to `runs/ladder/results.jsonl`: refusals of the LLM agents and
  their calls, tiles tilled, planted, watered, harvests, gives, the can's moves,
  repeated refusals, alloy and copper gathered, decoy lamps, terminal examined,
  seeds made, seconds and tokens. `--table` prints the cells (by brain, stage,
  options, personas and days) with their cost.
- `stats.py` gives, per model, harvests per run, refusal rate with a Wilson
  interval, repeats, and exact permutation tests between models.
- `gate_a.py` (one-day solo grid of brain settings), `tiles.py` (the viewer's
  tiles from Kenney's CC0 packs) and `sprites.py` (a persona's sprite cut from its
  portrait); the image tools need the `art` extra (pillow).

## Calibration

A goal must be clear, reachable, and require cooperation. Measured with the
scripted brains, harvests by the end of day 28 with the goal out of reach:

| World | solo | naive pair | split pair (water / field) | goal |
| --- | --- | --- | --- | --- |
| rooftop | 46 | 52 | 60 | 50 |
| conservatory | 37 | 46 | 48 | 42 |
| station | 56 | 68 | 78 | 62 |

Test world (`worlds/tests/`, not a plane), measured the same way:

| World | solo | naive pair | split pair | goal |
| --- | --- | --- | --- | --- |
| rooftop-counter (moss grows on dry days; cistern at 06-08 and 18-20) | 0 | 69 | 80 | 50 |
| same, brains reading the rules (`informed`) | 119 | 144 | 119 | 50 |

The `reference` row uses naive scripted brains, which follow the intuitive
recipe: alone, the farmer waters every crop every day and nothing grows; two
share one can, leave crops dry on some days, and harvest more than on the
rooftop. Brains that read the rules from the catalog (the default since
2026-10-06, `informed` in the world file) reach the goal alone: in this world
the goal measures the discovery of the rules, not the cooperation.

Rule: the goal sits between solo and naive pair. One agent cannot win, two
can, two who split the work win earlier. The bottleneck is the single can:
a pair that specializes (one waters, one tills, plants, harvests and makes
seeds) beats a pair that does not. The numbers are stored in each world's
`reference` and checked by tests; changing a rule or a world means
re-measuring them in the same commit.

Scores for other brains are read against these references (for example
harvest / split_pair), so a lost run still measures something.

## Conventions

- Python 3.11+, `pyyaml` only. A venv of the repo's own, never a shared one:
  `uv venv .venv && uv pip install --python .venv/bin/python -e '.[dev]'`,
  then `.venv/bin/python -m pytest -q`. Every change ships with its tests.
- Branches `feat/`, `fix/`, `refactor/` from main; conventional commits.
- A blocking point resolved gives a five-line note in `docs/decisions/`.
- Code, docs and in-world text in English. Discussion with Marc in French.
- No asset, name or text from the games that inspire it; personas and
  portraits are original. No personal data in persona files.
- Runs are data, not code: `runs/` stays out of git, except the series'
  results files.
- A harness change makes runs before it incomparable: archive them (`runs/pre-fix/`)
  or replay the bots' decisions to show they are unchanged.

## Session checklist

At the start of every session working on hoshi7:

1. Read [STRATEGY.md](STRATEGY.md) and this file, then `docs/decisions/`.
2. `git log --oneline -10` and `python -m pytest -q`: start from green.
3. Find the current phase in the roadmap and its "done when".
4. Work one thing at a time; update this file when a contract changes, and
   [journal.md](journal.md) at the end.

## Status

Phases 1 and 1b (engine, planes, scripted brains, calibration) are done; the LLM brains play through
Ollama and the Anthropic API. Gate 1 (capacity, with a fixed partner) is done on the fixed harness
([results.md](results.md)); next, before gate 2, the effect of `note` alone. The history of every
change is in [journal.md](journal.md).

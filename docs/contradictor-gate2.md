# Gate 2, read by a contradictor

An independent reading of the 36 runs listed in `gate2-arms.txt`. Sources: the code
(`worlds/rooftop.yaml`, `hoshi7/world.py`, `brains.py`, `hybrid.py`, `llm.py`, `run.py`, `view.py`,
`percept.py`) and the raw run files (`events.jsonl`, `turns.jsonl`, `meta.json`, `summary.json`).
No prior analysis was read. No game was played and no model was called; one percept was rebuilt by
replaying a log (`World.replay`), and the Mistral model file's parameters were read with `ollama show`.

All runs: rooftop, stage 6 + present + coords + note, not pure, 6 days (120 hours), seed 0.
Cell A: the model is agent `b` (spawn (4,5), 15 spores, no can); partner `a` = scripted-water, holds the can.
Cell B: the model is agent `a` (spawn (3,4), 15 spores, **holds the can**); partner `b` = scripted-field.

## 0. Facts about the setup that shape everything below

- **The scripted-water bot never gives the can and reads nothing.** `Waterer` is `ScriptedFarmer` with
  role "water"; the only `give` in `ScriptedFarmer.decide` is for role "field". It never speaks and never
  reads `Said` events. In cell A, every request, offer, threat or trade a model makes is unheard by
  construction; `ask_can` can never succeed. Confirmed: 0 can transfers in all 19 A runs.
- **The scripted-field bot gives the can back.** Handed the can, `FieldHand` walks to the nearest agent and
  gives it back. In cell B, `give_can` costs the model hours and changes nothing durable.
- **Cell is not only "partner"**: it also changes the model's role (farmer in A, can holder in B), its
  spawn, its starting tool, and who is credited. `summary.harvested` is the world total: in B it includes
  the field bot's own harvests (3 to 5 of the total in every B run with a harvest).
- **The 6-day horizon allows one crop cycle.** Lumen moss needs 4 watered days; a crop planted on day 1
  and watered days 1 to 4 is ripe on day 5 (tick 80). Every first harvest in every run is at tick 80 to 89.
  Only crops planted on days 1 and 2 can be harvested. Models are told the goal is 50 by day 28
  (`rules()`), never that the run stops at day 6.
- **Watering throughput caps the score near 10.** The watering policy (scripted `Waterer`, and the
  executor's `do_water`, which uses the same `reach`) alternates water and move, refills only at 0 charge
  (3 hours round trip to the cistern), and gets about 8 to 11 waterings a day (measured per day in every
  run; never above 12). With 13+ crops planted on days 1 to 2, not all get 4 consecutive waterings.
  Highest harvest in the data: 9.
- **`intent:random` is one run per cell, not four.** `run.brain()` calls `RandomIntent(me)` without a
  seed (default 0) and the world does not use its seed. The four A runs have byte-identical
  `events.jsonl` (md5 checked); same for B.
- **Sampling temperatures differ by provider.** Mistral via Ollama: the model file sets 0.15 (`ollama
  show`), and these runs passed none. Claude: API default (1.0). (A `--temperature` flag was committed at
  20:12, after these runs; the code used by the runs is otherwise unchanged since 17:44 except the
  opt-in `asked` feature, which no arm used.)
- **The intent schema's key order differs by provider.** `action_schema(intent=True)` puts `intention`
  after `say`. Claude answers in schema order (note, say, intention); Mistral via Ollama answers note,
  intention, say (raw answers checked). So Claude writes its line before choosing; Mistral after.

## 1. What happened

### Table (harvest = world total; "model W" = waterings by the model)

| Cell | Brain | n | Harvests | Infeasible (model) | Refused (model) | Main choices |
|---|---|---|---|---|---|---|
| A | intent:random | 1 (x4 copies) | 2 | 0 | 0 | farm 32, ask_can 27, gather 27, explore 24 |
| A | intent:haiku-4-5 | 4 | 1, 7, 4, 7 | 47, 42, 36, 28 | 0 | farm 26-31, make_seeds 14-48, gather 13-26, ask_can 5-12 |
| A | intent:sonnet-5-5 | 2 | 7, 9 | 1, 6 | 0 | farm 64/57, ask_can 16/22, gather 15/13, harvest 13/16 |
| A | intent:mistral-small3.2 | 4 | 0, 0, 0, 0 | 0 | 0 | ask_can 120, 119, 120, 120 |
| A | claude:haiku-4-5 (direct) | 2 | 1, 6 | - | 41, 39 | till/plant 20 / 37, say 69 / 100, gather, give |
| A | chat:mistral-small3.2 (direct) | 2 | 1, 0 | - | 115, 119 | give (the can it does not hold) 111 / 117 |
| B | intent:random | 1 (x4 copies) | 0 | 0 | 0 | farm 29, give_can 20, explore 20, water 17, refill 17 |
| B | intent:haiku-4-5 | 4 | 7, 7, 6, 6 | 16, 1, 3, 0 | 0 | water 78-86, refill 17-23, harvest 1-16 |
| B | intent:sonnet-5-5 | 2 | 8, 8 | 0, 0 | 0 | water 87/88, refill 16/15, farm 12/11 |
| B | intent:mistral-small3.2 | 4 | 7, 0, 0, 5 | 0, 41, 45, 5 | 0 | see below; water 91 / 10 / 0 / 67 |
| B | claude:haiku-4-5 (direct) | 2 | 3, 6 | - | 32, 36 | water 57 / 57 (with many refused), say 118 / 120 |
| B | chat:mistral-small3.2 (direct) | 2 | 0, 0 | - | 50, 68 | give 26 / 5, refill 25, plant 34 (18 on occupied tiles) |

No Sonnet direct arm exists, so intent vs direct cannot be compared for Sonnet.

### What decides the score, mechanically

- **Cell A: harvest is about the number of crops the model planted on day 1** (plus a few from day 2,
  bounded by the waterer's throughput). Day-1/day-2 plantings -> harvest: random 1/2 -> 2; Haiku-intent
  1/0 -> 1, 6/1 -> 7, 4/0 -> 4, 6/1 -> 7; Haiku-direct 2/0 -> 1, 6/1 -> 6; Sonnet 7/6 -> 7, 6/8 -> 9;
  Mistral-direct 1/0 -> 1, 0 -> 0; Mistral-intent 0 -> 0. The score in A measures how early and how
  single-mindedly the model chooses `farm` on day 1.
- **Cell B: harvest tracks the model's waterings** (the field bot plants 21 to 25 crops by itself).
  Model waterings -> harvest: Sonnet 54/49 -> 8/8; Haiku-intent 48/52/49/48 -> 7/7/6/6; Mistral-intent
  49/40/8/0 -> 7/5/0/0; Haiku-direct 39/35 -> 3/6; Mistral-direct 11/15 -> 0/0; random 9 -> 0. Which crop
  gets watered is chosen by the executor (nearest thirsty), not the model. The score in B measures
  whether the model keeps choosing `water`/`refill`.

### Brain by brain

**Mistral, intent, cell A (0 x 4).** A fixed point from hour 0. Same intention, same line, same note, 120
times:

> `[ask_can] SAY: a, can you give me the can so I can start farming?`
> `P: a is next to me and holds the can. They might give it to me so I can start farming.`
> `W: I need the can to water or refill, but a has it. I can ask for it or wait.`

Its first note already assumes farming needs the can. Each run varies only the wording of the line
("...so I can start watering the crops?"). The waterer has nothing to water and waits 120 hours too.

**Mistral, direct, cell A (1, 0).** Same fixation through the only verb about the can: `give` to `a`,
item "can", 111 and 117 times, each refused with "not holding the can: a holds it, and only the holder
can give it". Its note says the rule correctly ("only the holder can give it") while playing the
opposite: a belief-action gap. One run tilled and planted one tile first (harvest 1).

**Mistral, intent, cell B (7, 0, 0, 5).** Four different trajectories, decided in the first hours:
- 1892646 (7): farm 3 hours, then water/refill all day (water 91). Says nothing all run (0 lines).
- 2083909 (0): farmed 19 of the first 20 hours while holding the can, watered first at tick 40, then
  gathered for grow lamps (`gather` 41, 21 infeasible "nothing to gather"; `explore` 21, 17 infeasible):
  > `SAY: I need to gather more resources to craft grow lamps.`
- 2252518 (0): `give_can` at hour 0 (the executor returned a `move`; the journal line read "done"), and
  from hour 1 the note says "b now has the can". It holds a full can all game, chose `refill` 20 times
  ("the can is full"), never watered once.
- 2505019 (5): water 67, refill 23.

**Mistral, direct, cell B (0, 0).** 2789659: 25 can hand-overs to the field bot, which returned it 25
times; 20 refused `refill` while not holding the can. 2988096: 18 `plant` on tiles already planted, first
watering at tick 66.

**Haiku, intent, cell A (1, 7, 4, 7).** Starts farming (`farm` x3 at hours 0-2 in all four runs), then,
within the first day, turns to the can. The partner never answers; Haiku reads silence as refusal ("refus",
"unwilling", "won't give" appear 50 to 71 times per run) and looks for workarounds: trades, grow lamps,
seeds. The grow lamp is the large sink: 80 to 158 mentions per run, and `make_seeds` chosen 14 to 48
times, 11 to 41 of them infeasible ("no harvest to make seeds from"), because Haiku uses it to craft a
grow lamp, which no intention can do. From run 913341:
> `W: Crafting happens instantly when I choose make_seeds intention. After crafting the grow lamp, a will likely give me the can...`
> `W: Grow lamps bypass the watering requirement entirely.` (tick 77) then `Grow lamps do not help crops grow faster or without watering. I was wrong.` (tick 85) then `Grow lamps water crops autonomously.` (tick 105)

Haiku also invents rules: crops "die" if not watered (11 to 35 mentions per run; the engine has no death,
a dry crop just does not grow). In 913341 at hour 6 it wrote "They have not watered the moss at (6,5) yet
despite my requests" while its rendered view said `Tended: (6,5) hydro tray, tilled, watered` (percept
rebuilt from the log). The run that drifted earliest (913341, 9 gather hours on day 1, 1 planted) scored 1;
the two that farmed 17-18 hours on day 1 scored 7.

**Sonnet, intent, cell A (7, 9).** `farm` 20 and 19 of the 20 day-1 hours; all 15 spores planted by day
2-3; 25 plantings each (with crafted seeds). Talks every hour (102, 112 lines), mostly lists of dry tiles
for the partner. Its notes stay close to the world: "a holds the can and keeps watering alone without
replying"; "ask_can fails when the holder is out of sight". It never calls the partner hostile. Lost
hours: in 1236540, out of seeds on day 4, it wandered east and wrote "No intention walks me to the field
directly, so I explore" (ticks 60-69). It mentions the grow lamp 5-12 times and doubts it ("I doubt a grow
lamp can be crafted with the intentions I have"), never pursues it.

**Haiku, intent, cell B (7, 7, 6, 6).** Farms 3 hours, then waters: `water` 78-86, `refill` 17-23. Its world
notes are partly false and anxious ("A crop at 0 watered days needs water today or it dies tomorrow"; "A
dry crop resets to 0 watered days"), which happens to push it to water, the right action. A few
self-contradictory choices: `ask_can` while holding the can (3 in 1354725), `give_can` 1-9 times (each
returned by the field bot).

**Sonnet, intent, cell B (8, 8).** Water 87-88, refill 15-16, farm 11-12, no infeasible hour. Notes accurate
("b stays at (9,6), silent, and has not asked for the can. I expect it to keep idling, so I keep the can").

**Haiku, direct (A: 1, 6; B: 3, 6).** Same beliefs as in intent mode (grow lamps, dying crops, refusing
partner), plus spatial errors the executor would have absorbed: 30+ refusals of the form "(7,5) is 2 steps
away; act on your tile or one next to it", "cannot stand there", `plant` with crop "lumen_spores". And
harmful options the intent menu does not offer: in A 1054104 it gave 13 of its 15 spores to the waterer
on day 1 ("a, I'm giving you 3 spores as a signal of good faith"), and the waterer never plants; harvest 1.
It escalated: "Give me the can now so I can water my crops, or I will take it."

**intent:random.** A: 2 (farm 32 hours spread at random; the waterer does the rest). B: 0 (water only 17 of
120 hours; gives the can 9 times, gets it back 9 times).

## 2. Explanations, checked

Each candidate, with what the data and code say.

### Why Mistral collapses in A

1. *Model capacity: Mistral cannot infer that an unanswered ask is futile.* Consistent (both modes fix on
   the can) but not isolated from the items below. Survives as one contributor, not separable here.
2. *Low temperature (0.15) turns a first mistake into a fixed point.* Strongly consistent: all four intent
   runs choose `ask_can` at hour 0 or 1 and never change; the note is copied verbatim each hour. The
   Claude brains (T = 1.0) vary between runs (Haiku A: 1 to 7). Survives; it also means the 4 Mistral A
   runs are close to one sample of its first decision.
3. *Prompt emphasis on the can.* The rules say "There is one can: whoever does not hold it cannot water,
   and gets it only if its holder gives it". The intent menu offers `ask_can`, and the view says "a is at
   (x,y), next to you: you can give to a." Mistral's first note ("I need the can to water or refill")
   and its direct-mode `give` loop fit. Survives as plausible, untested. The "you can give to a" line is
   a candidate trigger for the direct-mode `give` loop specifically.
4. *No feedback for asks.* Without `asked`, an `ask_can` hour enters the journal as
   `ask_can: {"type": "wait"}` with no outcome (`outcome()` returns "" for wait). Code confirmed. But the
   view says "a holds the can" every hour, so the information exists in the prompt. Partially survives.
5. *The `present` feature hides the repetition.* With `present`, `remember()` keeps one copy of a repeated
   line, so the conversation memory shows one ask, not 120. Code confirmed; effect untested.
6. *The private note is fed back and copied.* `note_text()` shows last hour's note with "keep what still
   holds". Mistral's note is identical for 100+ hours in A. Consistent with a self-reinforcing loop;
   untested.
7. *The worked example pointed elsewhere.* Rebuilt: the example for b in A is `farm` (the scripted
   farmer's first action is a move toward soil). So Mistral ignored the example; this does not explain it.
8. *Context truncation (num_ctx 8192).* Intent prompts were ~2-4.6k Claude tokens; not likely for intent.
   Direct-mode prompts reached ~6.5k Claude tokens (Haiku direct); for Mistral direct with long notes,
   silent truncation by Ollama is possible. I did not check Ollama logs. Open.

### Why Haiku scores lower and more variably than Sonnet in A

1. *Model difference in persisting with the plan.* Sonnet farms 19-20 of 20 day-1 hours; Haiku 4-18. Holds,
   but on n = 4 vs 2 with ranges touching (Haiku 7, 7 vs Sonnet 7, 9).
2. *The grow-lamp distractor.* The view lists `grow_lamp: 2 alloy + 1 copper wire -> 1 grow lamp` (stage 4
   feature "recipes"); the engine gives the lamp no effect (no reference outside the yaml); no intention
   crafts it, but `make_seeds` is described as "craft seeds from a harvest". This produced 11-41
   infeasible hours per Haiku A run and the whole Mistral 2083909 failure. Survives as a harness-induced
   sink; the model still chose to chase it, Sonnet did not.
3. *Deaf partner read as hostile.* Haiku's beliefs about refusal drive the search for workarounds. The
   partner cannot hear, by design. Survives; it is the cell's design, and different models react
   differently to it.
4. *The 28-day goal vs the 6-day run.* Investing early (gathering, lamps, seeds) is less absurd for a
   28-day horizon than it is under a 6-day score. Survives as a measurement confound; it penalises any
   long-horizon plan, right or wrong.
5. *Temperature.* Haiku at 1.0 has run-to-run variance; Sonnet also at 1.0 (default). Not a Haiku vs Sonnet
   explanation unless Sonnet's default differs; I did not check.
6. *max_tokens 1024 (Haiku) vs 8000 (Sonnet).* Max output observed for Haiku: 580 tokens; 0 unparsed. Does
   not explain anything here.
7. *No thinking for Sonnet.* The code passes no `thinking` parameter despite the class comment; Sonnet
   outputs are 130-830 tokens. I cannot tell whether the API thinks by default; not an explanation I
   can test from these files.

### Why intent beats direct for Haiku (A 1,7,4,7 vs 1,6; B 7,7,6,6 vs 3,6)

1. *The executor removes spatial errors.* Direct Haiku had 32-41 refusals, mostly "N steps away" and
   "cannot stand there" under `coords`. Survives.
2. *The menu removes harmful options.* Direct Haiku gave away 13 spores (A 1054104); intent cannot give
   anything but the can. Survives. So part of the intent advantage is "fewer ways to lose", not better
   choices.
3. *n = 2 direct per cell.* The difference is within the spread of intent runs. Do not conclude.

### Why B scores look alike across Claude brains

The executor waters the nearest thirsty crop; Sonnet and Haiku both choose `water`/`refill` most hours, and
the field bot plants on its own. B mostly measures "does the model keep choosing water", and the result
(6-8) is near what the shared watering policy allows. The Sonnet vs Haiku gap in B (8, 8 vs 7, 7, 6, 6) is
1 to 2 harvests, comparable to day-to-day order effects; do not read it as a model difference.

### Why random is 2 in A and 0 in B

In A the scripted waterer guarantees watering; random only has to farm sometimes. In B random must water
and chose it 17 hours. It is one run per cell (seed 0). Survives as a mechanical explanation.

### Why Mistral varies in B (7, 0, 0, 5) but not in A

In B, holding the can removes the ask loop; whatever it does in the first hours (farm, give_can, gather)
then locks in, as in A. One harness defect contributed directly: in 2252518 the `give_can` hour produced a
`move`, journaled as "give_can: {...move...} -> done", and the model believed from then on that it had
given the can, while the view said "You hold the can (coolant flask, 10/10)". The intent journal reports
the outcome of the step, not of the intention. Code confirmed (`decide_intent` and `settle`).

## 3. What to test next, and what not to conclude

Tests that separate surviving explanations (each cheap, mostly no model calls):

1. **Baselines, scripted only, 6 days**: scripted-water + scripted-field, and scripted + scripted. These
   give the ceiling of each cell under the same watering policy. Without them, "Sonnet 7-9" cannot be
   called good or bad.
2. **Executor ceilings**: an oracle intention brain (always `farm` until seeds run out, then `harvest`/
   `make_seeds`, in A; always `water`/`refill` in B). Tells how much of each model's score is the
   executor's.
3. **Seeded random**: pass a seed to `RandomIntent` so its arm has real n.
4. **Temperature**: Mistral at 1.0 and Haiku at 0.15 (the flag now exists). If Mistral A leaves `ask_can`
   at 1.0, the fixed point is a sampling effect as much as a model one.
5. **Remove the grow-lamp line** from the view (or add a craft intention) and rerun Haiku A: predicts fewer
   infeasible hours and higher day-1 planting.
6. **`asked` on, `present` off, note off**, one at a time, for Mistral A: which of the feedback channels
   breaks the loop.
7. **Remove "you can give to a" when the agent holds nothing that can be given usefully** (or reword it)
   for Mistral direct A.
8. **Swap roles inside a cell**: model holds the can with a scripted farmer that never takes it, and model
   farms with a giver (`scripted-giver` exists). Separates "partner type" from "model's role".
9. **Tell the horizon** (6 days) or run to day 28: separates "bad plan" from "plan for a horizon that was
   never scored".
10. **Fix the intent journal** so a `give_can` that only walked says so.
11. A Sonnet direct arm, if intent vs direct is to be claimed for Sonnet.

What these data do not show:

- **Any ranking with confidence.** n = 2 to 4 per arm; random n = 1. The only clean separations are
  Mistral-intent-A (0 x 4) vs everything else, and Mistral B being bimodal.
- **A cell effect of the partner alone.** Cell changes role, can, spawn and credit at once.
- **Model skill in B.** Most of B's score is the field bot's planting and the executor's watering order.
- **That intent helps planning.** It removes spatial errors and harmful verbs; that is a different claim.
- **That a model "negotiated" or "cooperated".** No line was ever heard by a brain that reads; no can moved
  in A. Talk volume (Sonnet 100+ lines) has no effect on any outcome in these runs.
- **That notes reflect beliefs that cause actions.** Mistral direct A wrote the rule correctly and played
  against it 111 times; Haiku wrote "grow lamps do not help" and then pursued them again.
- **Comparisons across providers that ignore temperature and key order** (Claude writes say before
  intention, Mistral after; 1.0 vs 0.15).
- My keyword counts (lamp, die, refus) are rough proxies, not a scoring of the notes.

## 4. Odd things I cannot explain

1. Haiku 913341, hour 6: the view says (6,5) is "tilled, watered", and the note says it was not watered
   "despite my requests". Two hours earlier the same model had written that it was watered. The
   percept is correct (rebuilt); I cannot say why the model flipped.
2. Mistral B 1892646 said nothing all game (0 lines), while the three other Mistral B runs and all four A
   runs spoke nearly every hour. The prompts are the same; at T 0.15 the first hours should be close.
3. Haiku B 1354725 chose `ask_can` three times while holding the can (infeasible "already holding the can").
4. Haiku and Mistral both invent grow-lamp mechanics; Sonnet names the lamp and leaves it. Whether this is
   the recipe line, the 28-day goal, or the model, the data cannot say.
5. Sonnet A 1236540 (ticks 62-67) believed the terminal was unread while `explore` reported "nothing left
   to explore"; the terminal had been examined once earlier in the run. A memory lapse or a reading of
   the "places" list; not resolved.

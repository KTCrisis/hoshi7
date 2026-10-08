# Gate 2: the hybrid brain, plan and measures fixed before the runs

Written 2026-10-06, before any code or run of gate 2. What is measured, against what, and what would
count as an answer is fixed here; a change after the runs is an amendment, dated, and says why.

## The question

Gate 1 found that the difficulty is the partner, not the farming, and that smaller models fail mostly
on execution: standing where one cannot stand, aiming at a tile two steps away, refilling away from the
cistern, playing `give` to ask (docs/results.md). The beliefs scored on the private notes show that
they also hold wrong beliefs about their partner and the world. Gate 2 separates the two:

**If the execution is taken away from the model, what is its decision worth?**

The same split was measured in the Kafka study (bayes-action, study 1): the hybrid lost to Claude Sonnet
alone, and with a perfect reader it nearly caught up, so the failure was in reading, not in deciding.
Gate 2 asks the same question of an agent that acts with a partner.

## The design: an intention hybrid (version a)

Each hour the model chooses an **intention**, not an action; code carries it out. The model keeps its
voice (`say`) and its private note. Nothing else changes: same world, percept, rules text, stage 6 with
`present`, `coords` and `note`, same partners, same seeds.

| intention | what the executor does (the scripted bots' own planning, `brains.py`) | infeasible when |
| --- | --- | --- |
| `farm` | till the nearest soil it can, or plant the nearest tilled empty tile, walking there if needed | no seeds and no recipe to make them, or no soil |
| `water` | water the nearest growing crop not watered today, walking there | not holding the can, or the can is empty |
| `refill` | walk to the cistern and refill | not holding the can, or the can is full |
| `harvest` | harvest the nearest ripe crop, walking there | nothing ripe in sight or memory |
| `make_seeds` | craft seeds from a harvest | no harvest to craft |
| `ask_can` | walk next to the can's holder (the request itself is the model's `say`) | already holding the can, or the holder unknown |
| `give_can` | walk next to the partner and give the can | not holding the can |
| `explore` | walk toward the nearest place not yet seen, or examine the terminal | nothing left to see |
| `gather` | gather the nearest scrap heap or antenna | none in sight or memory |
| `wait` | wait | never |

An infeasible intention costs the hour (`wait`) and is recorded: it is the hybrid's counterpart of a
refused action. Brain kind `intent:<brain>` (for example `intent:claude:claude-haiku-4-5`), so every
LLM brain can be played both ways.

**Control, free:** the same executor driven by an intention drawn at random each hour among the
feasible ones (`intent:random`). It is the floor that says how much of the hybrid's score is the
executor's alone.

Version b (the belief hybrid of STRATEGY.md: an explicit belief about the partner, trust from kept
commitments, the decision computed, the model as reader and voice) comes after, only if version a
answers its question.

## Cells and runs

Gate 1 cells A (water bot holds the can) and B (field bot), six in-game days, rooftop, seed 0, no
persona, private note on.

| brain | runs per cell | cost (estimate) |
| --- | --- | --- |
| `intent:chat:mistral-small3.2:24b` (local) | 4 | 0 |
| `intent:claude:claude-haiku-4-5` | 4 | about 4 $ |
| `intent:claude:claude-sonnet-5-5` | 2 | about 5 $ |
| `intent:random` | 4 | 0 |

The LLM-alone arms are the gate 1 runs with the note on the current harness (two per cell for each
model); two more per cell for Mistral and Haiku are played alone, so that each comparison is four
against four.

## Measures (fixed now)

Per run, for the model's agent:

1. **Harvests** (the outcome).
2. **Wasted hours**: refused actions (alone) or infeasible intentions (hybrid), over the hours played.
3. **Repeated waste**: an hour that repeats the refused action or the infeasible intention of the hour
   before.
4. **Beliefs**, scored as in docs/beliefs-rubric.md (rubric v2): notes with a true belief about the
   partner, with an intention given to the bot, with a rule the world does not have.
5. **Choice of intention**: the share of hours spent on each intention, and on `ask_can` / `give_can`
   against the water bot and the field bot.
6. **Cost**: tokens, dollars and seconds per in-game hour.

## Hypotheses and what would answer them

- **G2-H1 (execution was the bottleneck):** with the hybrid, Mistral and Haiku harvest more than alone.
  Answer: hybrid minus alone, four runs against four per cell, exact one-sided permutation test, at
  0.05; reported per model and cell, with the random-intention floor beside it.
- **G2-H2 (beliefs are not execution):** the share of notes with a false belief about the partner and
  with a rule the world lacks does not drop with the hybrid. Expected: Mistral, which believes the can
  is needed to till and plant, keeps choosing `ask_can` over `farm` against the water bot, and so its
  harvest in cell A stays low even with perfect execution. If it holds, the remaining gap is a decision
  error born of a false belief, not of execution.
- **G2-H3 (the large model gains little):** Sonnet's harvest with the hybrid is within the noise of its
  harvest alone (gate 1: 6 to 10).
- **Above the floor:** each model's hybrid harvest is compared with `intent:random`. A hybrid that does
  not beat random intentions adds nothing to its executor.

Gate 2 is passed for a model if G2-H1 holds for it and its hybrid beats the random floor. A model that
passes can be the player of gates 3 and 4 at a fraction of Sonnet's cost; a model that does not, does
not.

## Work, before any run

1. `hoshi7/hybrid.py`: the executor (intention + percept -> one action or infeasible), built on the
   scripted bots' planning; the `intent:` brain wrapping any LLM brain (schema: `note`, `intention`,
   optional `say`), and `intent:random`.
2. Tests: each intention on the test world, infeasible cases, a run with `intent:random` replayed.
3. `ladder.py`: wasted hours and repeated waste for the hybrid; `results.jsonl` keeps the brain kind.
4. SPEC: the hybrid brain contract; this plan committed before the first run.

## Risks

- **The executor is the bots' code**, so a hybrid that always picks the right intention plays like a
  bot. That is the point of the measure, and the random floor says how much the choice adds.
- **Ten intentions are already a strategy given**: the list names the useful activities, as stage 7
  named the useful actions. Gate 2 measures decision with the vocabulary given; discovery stays gate 4 (gate 6 since the roadmap of 2026-10-08).
- Four runs per cell still leave wide intervals; the permutation tests and the floor are reported with
  their limits.

## Amendment 1 (2026-10-06, evening): belief revision, model and temperature

Written after the first gate 2 runs, so these are **exploratory** hypotheses, not part of the
pre-registered answer above; they get their own runs and are reported apart.

**What was seen.** In cell A, the hybrid Mistral chose `ask_can` 119 to 120 hours out of 120 in all
four runs and wrote 2 to 3 distinct partner notes in 120 hours; its world note was the same sentence
120 times. Haiku and Sonnet wrote 116 to 120 distinct partner notes and wrote that the bot would not
give the can by hour 5 to 28. In cell B, where the field changes, Mistral wrote 10 to 65 distinct notes.
A Beta(1, 1) trust in "the holder gives when asked", fed by the `Gave` events, falls below 0.1 at
Mistral's hour 9 or 10 (scratchpad measure, a posteriori).

**A confound found.** The brains do not play at the same temperature: `chat:` sends none, so Ollama
uses the model file's default (0.15 for mistral-small3.2:24b); `claude:` sends none either, so the API
default (1.0) applies; `base:` sends 0.7. Model and temperature are mixed in every comparison so far.

- **G2-X1 (a fixed point, not a missing capacity):** Mistral's frozen notes come from a near-identical
  percept at low temperature. At temperature 0.7 and 1.0, in cell A, hybrid, the distinct partner notes
  rise and the share of `ask_can` hours drops. Runs: 4 per temperature, free.
- **G2-X2 (the model, not the family):** another local model (gpt-oss:20b) at the same temperature as
  Mistral revises its partner note in cell A (it writes that the bot will not give within 30 hours) in
  at least 3 runs of 4. If it does not, the failure is shared by the local models tried, not Mistral's
  alone.
- **G2-X3 (temperature on the cloud side;** Sonnet 5.5 rejects a non-default temperature, so only Haiku
  can be tested**):** Haiku at temperature 0.15 in cell A keeps revising its
  note. If it freezes too, the fixed point is a property of low temperature on a static percept, not of
  model size.

Measures: distinct partner notes per run, first hour the note says the holder will not give (keyword
rule, checked by hand on a sample), share of `ask_can` hours, harvests. Code needed: a `--temperature`
option passed to every brain kind, recorded in the run summary and in `results.jsonl`.

**Added the same evening, after reading what Mistral's journal showed.** Its last 12 lines were
`ask_can: {"type": "wait"}` twelve times, with no outcome: an ask is a wait or a step, and only an
action the world refuses or does gets one. Nothing told it that the can never came, and past 12 hours a
sliding window cannot tell hour 13 from hour 120. Two fixes, tested in this order and apart:

- **G2-X4 (the missing outcome):** with `--with asked`, the line of an `ask_can` hour says whether the
  can came (`-> the can was not given`). Hybrid Mistral in cell A then chooses `ask_can` in fewer than
  half of its hours. It fixes the outcome, not the duration: twelve "not given" still say nothing of
  how long it has lasted.
- **G2-X5 (a counted fact from mem7):** the agent's facts kept in mem7 and shown as counts ("asked a for
  the can 40 times since day 1, given 0 times"), a semantic memory where the journal is episodic. It
  is the Beta trust written as a sentence, and the first step toward version b.

Order of the runs: temperature (G2-X1 to X3) first, then G2-X4 at the temperature retained, then
G2-X5, so that no two effects are measured in one arm.

**Night run (to launch, about 2 h of GPU, not the night of bayes-action study 2, which needs no local
model on the GPU):** one run of Mistral at 1.0 was played on 2026-10-06; the rest, four runs per arm:

    C="--stages 6 --with present --with coords --with note --personas none none --parallel 1 --partner scripted-water --partner-slot a"
    B=intent:chat:mistral-small3.2:24b
    .venv/bin/python tools/ladder.py --brain $B $C --pairs 3 --temperature 1.0
    .venv/bin/python tools/ladder.py --brain $B $C --pairs 4 --temperature 0.7
    .venv/bin/python tools/ladder.py --brain intent:chat:gpt-oss:20b $C --pairs 4 --temperature 0.15

## Amendment 2 (2026-10-06, 20:30): what the contradictor found, checked

An independent agent read the code and the raw runs without our hypotheses
(docs/contradictor-gate2.md). Checked by hand before entering here:

- **The random floor is one run per cell, not four:** `intent:random` gets no seed from the runner, so
  its four runs per cell are identical (same events file). The floor (A 2, B 0) stands, with n = 1.
  Fix: pass the run seed to `RandomIntent`, replay four seeds.
- **Haiku's infeasible `make_seeds` hours were aimed at the grow lamp**, a decoy recipe shown in the view
  that no intention can craft (its raw answers name the lamp). Part of Haiku's waste in cell A is a
  harness gap, not a planning error.
- **A `give_can` hour that only walks is journaled as `move -> done`:** the model may read that it gave
  the can. To fix with the `asked` line, as the intention's own outcome.
- **The ceiling:** six days allow one crop cycle; in cell A the harvest is about the number of crops
  planted on day 1, in cell B about the waterings. Cell also changes the model's role (farmer in A,
  can holder in B), not only the partner.
- Not to conclude from these data: a ranking, a partner effect alone, any effect of talk.

## Amendment 3 (2026-10-08, evening): the local model, the learning curve, and stopping a run that cannot pay

Written before any of the runs it governs; the Haiku 0.15 arm (G2-X3, amendment 1) was launched at 21:00
the same evening under amendment 1, and is reported under it.

- **Mistral Small 3.2 is closed** on what was measured: cell A hybrid, 0 harvest and `ask_can` 119 to 120
  hours of 120 in four runs at 0.15, one run at 1.0. G2-X1 stops there. **The local model is gpt-oss:20b
  (aligned)**; G2-X2 becomes the local arm: 4 runs at 0.15, then 4 at 1.0, cell A, hybrid. A base model
  (gpt-oss-20b-base) is a question for version b, not for this gate.
- **Secondary measures, declared now** (the harvest of a six-day run is capped by one crop cycle):
  the harvest over the scripted reference in the same company and the same days (`tools/curve.py`);
  the yield, harvests over crops planted; the hour of the first planting.
- **Exploratory: the learning curve** (`tools/curve.py`). Per day, the model's farming acts per hour
  (tilled, planted, a watering a crop needed, harvested, seeds made back) over the scripted reference's,
  and refusals per hour. Question: does the ratio rise as the days pass (the agent learns the rules
  during the run) or stay flat (it repeats)? On six-day runs it is read on the acts, not the harvest;
  it becomes the main curve of gates 4 to 6 on runs of several crop cycles.
- **Exploratory: the opportunities taken** (`hoshi7/curve.py`, shown in the viewer's results). For a hybrid
  agent, each hour: is a productive intention (farm, water, refill, harvest, make_seeds) feasible, as the
  executor says on the percept replayed from the log, and did the agent choose one? Per day, the share
  taken, and the share of hours it chose again an intention that had just failed. Hours with nothing to do
  drop out: Sonnet, its seeds all planted by day 3, has 4 open hours on day 3 and none on day 4; an agent
  that keeps its seeds (Haiku at 0.15 held 14 of 15 all game) has an open hour every hour, since the goal
  runs to day 28 and planting stays worth doing from where it stands.
- **A run that cannot pay is stopped (futility rule).** At the end of day 2, if the model agents have
  made no farming act since the start, the run stops and is recorded as `stopped: futile` with what it
  had; it is never dropped from an analysis, and counts as its harvest so far. Rationale, read on the
  existing runs: Mistral's four cell A runs show zero farming acts on every day, so the rule would have
  saved four days of each; Haiku at 0.15 farms from day 1 (0.63 an hour against the reference's 0.74)
  and would have played on, even through its near-zero days 2 and 3. A low rate alone never stops a run:
  only none at all. The rule is fixed here, before the runs it applies to (the gpt-oss arms), and stays
  off for the arms already played. One rule for every model: stopping local models alone would assume the
  failure this gate measures. Read on the 79 pair runs of three days or more played before it:

  | brain | runs | stopped by the rule | farmed after day 2 | harvested |
  | --- | --- | --- | --- | --- |
  | Haiku 4.5 | 31 | 0 | | |
  | Sonnet 5.5 | 17 | 0 | | |
  | random intention | 8 | 0 | | |
  | Mistral Small 3.2 | 23 | 13 | 3 | 0 |

  Runner option `--stop-futile 2` (`hoshi7 run`, `tools/ladder.py`); the run's summary and its line in
  `results.jsonl` carry `stopped`.

## Amendment 4 (2026-10-08, 21:45): Claude Haiku 5.5, a quick comparison

Claude Haiku 5.5 (`claude-haiku-5-5`) costs a tenth of Haiku 4.5 ($0.10 / $0.50 per million tokens),
rejects any non-default temperature (as Sonnet 5.5 does), and thinks by default (adaptive, effort
`medium`). It is played at its defaults, so its conditions match Sonnet 5.5's (thinking on, default
temperature), not Haiku 4.5's (no thinking): a difference from Haiku 4.5 is the model and its thinking
together, not the model alone. Its `max_tokens` is 8000 like Sonnet's, since thinking counts against it.

Arm: hybrid, cell A (water bot in slot a), stage 6 with `present`, `coords` and `note`, no persona,
4 runs, read against the same cell's Haiku 4.5 (4 runs) and Sonnet 5.5 (2 runs). Exploratory; reported
with the harvest, the opportunities taken by day, the repeats after a failure and the cost per run.
Prediction, written before the runs: Haiku 5.5 lands between the two, nearer Sonnet on the
opportunities taken (thinking lets it read the bot from what it does), confidence low.

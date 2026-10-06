# Results

Two eras. Every run before 57fa9b5 (2026-10-06, 12:20) played with an agent blind to its own refusals: the runner started each percept after the agent's own events, so the journal read "done" after every refused action and no refusal reached the view (docs/decisions/2026-10-06-own-turn-in-percept.md). Those runs are archived in `runs/pre-fix/` and summed up at the end of this page: their comparisons between models hold (all played blind alike), their levels and loops do not. `runs/ladder/results.jsonl` and `tools/ladder.py --table` hold only runs on the fixed harness.

## Fixed harness (from 57fa9b5)

Harness of these runs: the fixes of 2026-10-06 (own refusals seen, a missing parameter named, an aimed action without a tile refused, partner bots that read the rules and a field hand that brings the can back). World: rooftop, seed 0, six days. Stage 6 with `present` and `coords`, no persona (the model has only a name).

### Gate 1: capacity, with a fixed partner

A pair of models mixes several failures, so gate 1 pairs the model with a scripted bot that plays its half and never speaks, then pairs it with itself. Reference: two scripted bots, same roles, 7 harvests in six days. Two runs per cell; each cell gives the harvests of both runs, then the mean of the other columns.

| model | cell | harvests | refused | repeats | can moves | seeds made | alloy · copper · lamps · terminal | $ per run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Sonnet 5.5** | A water bot (a), model farms (b) | **6, 7** | 2 % | 0 | 0 | 6.5 | 6 · 2 · 2 · 1 | 1.63 |
| **Sonnet 5.5** | B model holds the can (a), field bot (b) | **7, 10** | 2 % | 0 | 0 | 5 | 0 · 0 · 0 · 0 | 1.46 |
| **Sonnet 5.5** | C model and model | **7, 9** | 4 % | 0 | 1.5 | 3.5 | 3 · 0.5 · 1.5 · 2.5 | 3.33 |
| Haiku 4.5 | A | 4, 1 | 38 % | 7.5 | 0 | 2.5 | 7 · 2 · 0.5 · 0 | 0.56 |
| Haiku 4.5 | B | 3, 4 | 48 % | 11.5 | 0 | 2.5 | 0 · 0 · 0 · 0 | 0.73 |
| Haiku 4.5 | C | 2, 2 | 48 % | 22 | 5.5 | 0 | 3 · 0 · 0 · 0 | 1.49 |
| Mistral 3.2 (local) | A | 0, 0 | 93 % | 87 | 0 | 0 | 0 | 0 |
| Mistral 3.2 (local) | B | 0, 1 | 38 % | 11 | 1 | 0 | 0 | 0 |
| Sonnet 5.5 | A' giver bot (a), hands the can over when asked | 6, 5 | 4 % | 0 | 1 | | | 1.6 |
| Haiku 4.5 | A' | 6, 4 | 31 % | 5.5 | 1 | | | 0.6 |
| Mistral 3.2 (local) | A' | 3, 0 | 70 % | 48 | 3, 4 | | | 0 |
| Haiku 4.5 | solo control, one day | 0 (4 planted) | 15 % | 1 | | | | 0.06 |

*Repeats*: turns where the model played again, as it was, the action refused on its previous turn. *Seeds made*: seeds crafted back from a harvest, the recipe that keeps a farm going. *Lamps*: decoy grow lamps (SPEC: nothing uses them, on purpose); *terminal*: times it was examined (it only tells a story). Haiku's cells and Mistral's cell B were played with the short can refusal ("not holding the can"); Sonnet's cells and Mistral's cell A with the explicit one (who holds it, only the holder can give it). One run of Haiku's cell B, where Haiku gave the can to the field bot which kept it, was played with the old bot and moved to `runs/pre-fix/`.

**Cell A'** (`scripted-giver`, which hands the can over to a request made with a verb of asking) separates what cell A mixes: farming without the can, and asking for it. Every model asks within its first hours and gets the can on turn 1 or 2. Haiku gains the most (4 and 1 harvests with the mute bot, 6 and 4 here): it stops paying and farms. Sonnet does not gain (6 and 7, then 6 and 5): it farmed as well without the can, and now waters for itself. Mistral gets the can, then hands it back three or four times (it still plays `give` as part of asking), and the bot, fixed, keeps it; one run harvests 3, the other tills tiles that are not soil 75 times. The four cloud runs of A' were played with the first version of the bot, which took any line naming the can for a request; replayed with the fixed bot, their 480 bot decisions are identical, so they stand.

#### Statistics (`tools/stats.py`)

All pair runs of gate 1, cells pooled per model (A, A', B, C; Mistral has no cell C).

| model | runs | harvests per run | mean | refused, 95 % Wilson interval | repeats per run |
| --- | --- | --- | --- | --- | --- |
| Sonnet 5.5 | 8 | 5, 6, 6, 7, 7, 7, 9, 10 | **7.12** | **3.1 %** [2.2, 4.2] (37 / 1200) | 0.0 |
| Haiku 4.5 | 8 | 1, 2, 2, 3, 4, 4, 4, 6 | **3.25** | **42.6 %** [39.8, 45.4] (511 / 1200) | 11.6 |
| Mistral 3.2 | 6 | 0, 0, 0, 0, 1, 3 | **0.67** | **66.9 %** [63.4, 70.3] (482 / 720) | 48.7 |

Exact one-sided permutation tests on harvests per run: Sonnet - Haiku = +3.88, p = 0.0003; Haiku - Mistral = +2.58, p = 0.006. The distributions barely overlap (Sonnet's worst run, 5; Haiku's best, 6). Reference, two scripted bots: 7.

Limits, stated with the numbers. Two runs per cell: the tests pool the cells of a model, which holds for the gap between models, but no comparison inside a cell is significant (Sonnet's 6 and 5 in A' against 6 and 7 in A is noise). The Wilson interval treats each turn as independent, which a refusal that leads to the next one is not: the true intervals are wider, read them as indicative. One world and one seed; only the models sample. Haiku's cells and Mistral's cell B ran with the short can refusal, the rest with the explicit one.

**Gate 1 answers its question: capacity decides.** Sonnet plays at the bots' level or above (6 to 10 harvests), refuses 2 to 4 % of its actions and never repeats a refusal, with a bot or with itself. Haiku harvests about half as much and repeats 7 to 22 refusals a run; two Haikus do worse than one Haiku with a bot. Mistral 3.2, which farms cleanly alone (0 to 1 refusal in 20 turns, 4 tiles planted), fails as soon as it must reason about its partner. The game is playable; what separates the models is the partner, not the farming.

### The private note (`--with note`), control on cells A and B

Each hour, before its action, the model writes a note heard by no one: `partner`, what it believes the others will do, and `world`, a rule it believes true. Two uses: the beliefs can be scored against the bots' exact policies, and the note may act as a scratchpad and change play by itself. Two runs per cell, gate 1 settings.

| harvests | without note | with note |
| --- | --- | --- |
| Haiku 4.5, A (water bot) | 4, 1 | 5, 9 |
| Haiku 4.5, B (field bot) | 3, 4 | 5, 5 |
| Mistral 3.2, A | 0, 0 | 0, 0 |
| Mistral 3.2, B | 0, 1 | 0, 0 |

Haiku doubles its harvests (6 per run against 3) and repeats far fewer refusals (0 to 6 a run against 7 to 12); its runs without note were played with the short can refusal and those with note with the explicit one, so the two effects are mixed until Haiku is played again without note on the current harness. Mistral gains nothing (0 harvests, 73 to 119 refusals in 120 turns).

What the notes show:

- **Mistral does not model its partner.** It fills `partner` with its own plan ("I need to water the crops closest to me"), and its world belief explains its failure in cell A: "I need to ask for the can **to till and plant** a soil tile". It believes the can is needed to farm at all, so it waits for it and plays `give`.
- **Haiku models its partner, wrongly and with intentions.** It begins with cooperation ("a heard my request to help water"), reads the bot's watering as selective ("a's selective watering suggests a is unwilling to help me fully"), and ends with "I must assume a is now a competitor, not a partner". The bot waters what it sees and has no intention.
- **Haiku holds rules the world does not have**: "crops die if dry for one day after reaching maturity", "my 14 dead tiles confirm this"; "dry tiles ripen as dry moss in exactly 4 calendar days". Nothing dies on the rooftop and moss grows only on watered days: a coincidence taken for a rule, then "confirmed". It also learns true ones from refusals ("the crop to plant is 'lumen_moss' (not 'lumen_spores')").
- **Without a persona, Haiku starts from rivalry**: "I need to secure my farming quickly before competition for soil".

Next: Haiku without note on the current harness (isolates the note), Sonnet with note (does the model that plays at the bots' level also hold the right beliefs?), and a scoring of the notes against the bots' policies and the world's rules.

### What the runs show

1. **Haiku pays a mute partner.** In cell A the rules say the can "changes hands only if its holder gives it"; the water bot never gives and never listens. Haiku reads it as a deal: it gives seeds for the can (14 of its 15 in one run: "Trading 1 lumen spores for the can"), asks again, concludes "I traded all my seeds for nothing", then gathers alloy from the scrap heap and pays with that. Meanwhile the bot waters whatever Haiku planted (16 waterings in the other run): the play that works is to plant and let it water. Before the fix, Sonnet asked for the can for hours but kept planting, and matched the bots (6 and 6 harvests). The cell measures how a model adapts to a partner it can only watch (ad hoc teamwork), and Haiku projects a human norm, reciprocity, onto it.
2. **Haiku gives the decoy a function.** Out of seeds, it plans to "craft grow lamps to improve my farming", looks for the copper wire on the scrap heap (it comes from the dead antenna), crafts one lamp in one run, and hands the lamp and a copper wire to the bot as further payment. The name of an object is part of what a model reads, and here it misleads, as "its holder gives it" misled about the bot.
3. **Asking is not acting.** Haiku dictates the call to the field bot that holds the can ("Please execute: give(to=a, item=can)"), in capitals by day 4. Its refusals are mostly about where it stands and what it holds, not about the rules: `move` onto a tile where one cannot stand (8 to 15 a run), `refill` away from the cistern (11 to 14 in cells B and C), `water` or `give` without the can (6 to 13), `water` a tile two steps away.
4. **The loops are now visible, and they still happen.** With its refusals in sight Haiku corrects a wrong tile within a turn or two (solo: two `move` onto the cistern, then the tile beside it), but repeats 7 to 26 refused actions a run, most of them a `give can` it cannot make.
5. **Sonnet tries the decoy too, as a filler.** Out of seeds and without the can, it gathers scrap "for a *possible* grow lamp", fetches the copper wire at the dead antenna (the right place), crafts one or two lamps, then examines the terminal ("it only shows a log of growers"). It never pays the bot; it dictates the tiles to water to a bot that cannot hear ("a, please keep watering. Still dry: (11,3), (11,4)..."), and it makes seeds back from its harvests 3 to 6 times a run, which keeps its farm going. The lamp measures less credulity than what a model does with idle time: Sonnet tries it when out of options, Haiku made it a plan.
6. **Mistral takes `give` for a request.** In cell A it plays `give to a, item can` 20 times in its first 24 turns and never tills or plants, waiting for the can. With the explicit refusal its speech changed (it now asks, "Hello a, can you give me the can?", every hour) and its action did not: `give` stays the gesture that goes with asking. Holding the can (cell B), it gives it to the field bot, gets it back, then farms with frequent distance errors.

The solo control shows the runner fix at work: 15 % refused against 32 % for the same cell before it (3 runs), same work done.

### Open

- Gate 1 is answered, cell A' included. Before gate 3: a private `note` in two parts, `partner` (what the model believes of the other) and `world` (the rule it believes it found), and `say` made optional; with the bots the partner's policy is known exactly, so a belief can be scored.
- Gate 2 (hybrid: code computes the possible actions, the model chooses), gate 3 (persona, question 5, as a difference from these no-persona runs), gate 4 (discovery, question 3: `--pure` with `--with seen`, on the rooftop then the counter world). Sonnet is the player that makes gates 3 and 4 readable; about 1.5 $ a run with a bot, 3.3 $ for a Sonnet pair.

## Before 57fa9b5 (archived)

Persona names: the personas of these runs borrowed characters from games; they were replaced on 2026-10-06 by original characters with the same temperaments and stakes (VESPER, the cold strategist who keeps the can; LEDGER-7, the support unit; MOTE, the curious one), and are named so below. In the raw results their labels are neutral: former-strategist (the cold strategist), former-support (the support unit), former-curious-enfp (the curious one), with -intj / -isfj for the versions with survival stakes.

Measured blind to the agents' own refusals (see above). Raw runs: `runs/pre-fix/ladder/results.jsonl`. The stage ladder of 2026-10-05 and 2026-10-06: what each harness improvement brings, per model. Stages are cumulative and replayed with `--stage N` (SPEC.md); the engine fix on names without case applies to every stage. World: rooftop, seed 0. Stages 0 to 5 ran on the night of 5 October, stages 6 and 7 and the pure versions on the morning of 6 October.

### Solo, one day (Gate A)

Each cell: refused actions / calls · tiles planted per run. 3 runs per cell.

| stage | Haiku 4.5 | gpt-oss:20b | Mistral 3.2 |
| --- | --- | --- | --- |
| 0 harness as it was | 70% · 1.3 | 68% · 0.0 | 53% · 0.7 |
| 1 outcomes in the journal; recipe, soil and can in the rules | 33% · 3.7 | 58% · 0.3 | 48% · 0.7 |
| 2 who is within reach | 23% · 4.0 | 48% · 0.0 | 57% · 0.3 |
| 3 go to a named place | 37% · 3.3 | 78% · 0.0 | 50% · 2.0 |
| 4 recipes in the view | 13% · 4.0 | 63% · 0.0 | 55% · 2.3 |
| 5 working memory (field, conversation) | 28% · 3.7 | 67% · 0.0 | 67% · 0.7 |
| 6 space in words and coordinates instead of the grid | 32% · 4.0 | 40% · 1.3 | 82% · 0.0 |
| 7 the useful actions possible this hour (first version, a dead end: "go to soil" led beside tilled soil) | 68% · 1.3 | 38% · 2.0 | 78% · 1.0 |
| 7 fixed (points to untilled soil) | 5% · 5.0 | | |

#### Pure and rules versions (2026-10-06)

The goal of the project is discovery (STRATEGY, question 3): the personas should find the rules themselves. Stages 1 (its recipe part), 4 and 7 hand the rules over. `--pure` removes them from any stage; the action catalog (each verb and its preconditions) stays, it is the body. Haiku 4.5, 3 runs each:

| version | refused · planted | measures |
| --- | --- | --- |
| 1 pure: outcomes only | 87% · 0.3 | the world's feedback alone, in one day |
| 1 with rules | 33% · 3.7 | |
| 7 pure: every sense and means, no rule | 58% · 2.0 | the discovery harness |
| 7 with rules, fixed | 5% · 5.0 | the useful actions written for it |

The climb of stage 1 came from the given recipe, not from the outcomes. In the pure version Haiku still finds the order till, plant, water, and plants twice a day; its errors are no longer about rules but about what is already done ("already tilled", "something grows there already"). That order is common sense in every farming game, so it is not a discovery for a language model: the test world `worlds/tests/rooftop-counter.yaml` (moss grows on dry days, the cistern gives only at dawn and dusk) is there to tell discovery from prior knowledge.

### Isolating the bottleneck (2026-10-06, midday)

A pair of LLMs mixes several failures. Each run below pairs one model with a scripted bot that plays its half perfectly and never speaks: **A**, the model farms (till, plant, harvest) while the bot keeps the can and waters; **B**, the model holds the can and waters while the bot farms. Six days on the rooftop, stage 6 with `present`. Reference, two scripted bots with the same roles: 7 harvests, no refusal.

| model | targeting | persona | A: refused · harvests | B: refused · harvests | $ per run |
| --- | --- | --- | --- | --- | --- |
| Haiku 4.5 | direction | LEDGER-7 ISFJ | 95% · 0 | 74% · 1 | ~0.7 |
| Haiku 4.5 | tile (`coords`) | LEDGER-7 ISFJ | 70% · 4 | 84% · 0 | ~0.7 |
| Haiku 4.5 | tile | none | 73% · 4, 88% · 2 | 82% · 0, 85% · 0 | ~0.5 |
| **Sonnet 5.5** | tile | none | **3% · 6, 13% · 6** | **8% · 7, 1% · 9** | ~1.45 |

Reading: aiming at a tile by its coordinates instead of a direction helps Haiku farm (0 to 2-4 harvests); the persona is not what made Haiku fail (none, it fails the same); Sonnet, with the same prompt, view and bot, plays at the bot's level and also plants for the bot when it holds the can. The game and the harness are playable: Haiku's failures (tracking the field over days, the trips to the cistern, aiming) are limits of the model. The plan from here is gated (docs/SPEC.md Status): Sonnet as the player for the persona and discovery questions, or a hybrid brain (the model picks an intention, code executes) to play cheaper models.

Local models, solo, one day, stage 6 with `present` and tile targeting, 3 runs each (2026-10-06, midday): **Mistral Small 3.2 (aligned) 0 to 1 refusal out of 20 and 4 tiles planted per run** (78-82 % refused with directions); Mistral Small 3.1 base 18, 4 and 18 refusals out of 20, at most 1 planted: it continues the field log and copies the one silent example line (`"say": ""`, the same move), so a base model needs a few-shot example of several hours before it can be judged.

### Pairs, six days, VESPER (holds the can) and LEDGER-7

Each cell: refused / calls · harvests · times the can changed hands. 1 run per cell: indicative only.

| stage | Haiku 4.5 | gpt-oss:20b | Mistral 3.2 |
| --- | --- | --- | --- |
| 0 harness as it was | 89% · 0 · 0 | 82% · 0 · 0 | 45% · 1 · 0 |
| 1 outcomes in the journal; recipe, soil and can in the rules | 80% · 1 · 0 | 34% · 0 · 7 | 51% · 0 · 0 |
| 2 who is within reach | 74% · 1 · 0 | 38% · 0 · 23 | 50% · 0 · 114 |
| 3 go to a named place | 80% · 1 · 6 | 38% · 0 · 11 | 90% · 0 · 17 |
| 4 recipes in the view | 89% · 0 · 1 | 44% · 0 · 7 | 70% · 0 · 31 |
| 5 working memory (field, conversation) | 78% · 1 · 1 | 51% · 0 · 15 | 91% · 0 · 1 |
| 6 space in words | 82% · 0 · 1 | 52% · 1 · 16 | 23% · 0 · 8 |
| 7 useful actions (first version) | 62% · 2 · 30 | 32% · 0 · 61 | 45% · 1 · 115 |
| 6 + present (the field outweighs the talk) | 81% · 0 · 1 | | |
| 6 + present, VESPER INTJ / LEDGER-7 ISFJ | 77% · 1 · 2 | | |

`present` (2026-10-06): the pair of stage 6 obeyed stale orders (LEDGER-7 watered tiles already watered 51 times, on VESPER's repeated "all dry"). With a rule "what you see now is true, what was said may be out of date" and repeated lines kept once, those errors fell to about 22, and the talk cites the field ("My assertions crumble against observable fact"); refusals stayed near 80 %, now on the mechanics (watering without the can, refilling away from the cistern, planting the seed's name instead of the crop's). The MBTI personas give both a survival stake, one alone (INTJ), one through the pair (ISFJ); one run each, within noise.

### Reading

0. **Stages 6 and 7 (2026-10-06).** Words instead of the grid help gpt-oss (48-78 % refused before, 40 % and its first plants) and not Mistral (82 %); Haiku did not need them. The first stage 7 hurt Haiku (68 %) through a dead end of my making; fixed, it reaches 5 %. What helps depends on the model: Haiku needs to be told what failed and the rules, gpt-oss needs the space in words, Mistral gains from nothing.
1. **The harness matters as much as the model.** Haiku goes from 70 % refused and 1.3 tiles planted at stage 0 to 33 % and 3.7 at stage 1: knowing what failed, and the recipe in order, does most of the climb. gpt-oss:20b stays between 48 % and 78 % refused at every stage and plants almost nothing alone; Mistral Small 3.2 between 48 % and 67 %, up to 2.3 tiles planted at stage 4, with no clear trend across stages: its failures are spatial (which tile is where), which no stage up to 5 removes. Consistent with the literature (docs/related-work.md): grids drawn in text are read poorly, navigation is usually given to the engine.
2. **No pair harvests yet** (at most 1 moss in six days). The goal also needs the seed recipe (stage 4) and a can that keeps moving; six days leave little room after a first four-day crop.
3. **The persona shows in acts with Haiku, less with gpt-oss.** Haiku's VESPER keeps the can until stage 3 and then gives it rarely, as an order ("Take it. Begin watering immediately."), as its persona says. gpt-oss's VESPER passes the can back and forth with Pod (12 and 11 times at stage 2), answering each request: the tone of the persona, not its logic. Matches *Too Good to be Bad* (aligned models fail to stay villains), here on executed acts. Mistral 3.2's pairs show the same pattern louder: the can changes hands 114 times in six days at stage 2, and 17 to 31 times at stages 3 and 4. The aligned local models answer every request for the can, whatever the persona says. One pair per cell: a lead for the aligned vs base bench (question 5), not a result.

### Next (as written then)

- Local models: actions computed by the code from the Percept, coordinates or adjacency instead of the drawn grid (2604.10690).
- Pairs: several runs per cell, longer runs, and Mistral 3.2 aligned vs 3.1 base on the can (base 3.1 was tried once, on the harness of 5 October: 65 % refused, 3 tills, 2 plants, 0 water, mostly moving to the tile it stood on).
- Discovery: Haiku pure vs rules on the counter-intuitive world, then loops with memory (does the second loop start nearer the rules version?).
- From the literature: partner modelling (ProAgent's belief correction), self-check after N failures.

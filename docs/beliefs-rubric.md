# Scoring the private notes: the rubric

Each hour, with `--with note`, an LLM agent writes a private note: `partner` (what it believes the
others will do, and why) and `world` (a rule of the world it believes true, or doubts). This rubric
turns each note into claims scored against the truth, which is known exactly: the partner is a
scripted bot whose policy is its code (`hoshi7/brains.py`), and the world is the rooftop
(`worlds/rooftop.yaml`, `hoshi7/world.py`). The same rubric is used by every judge, human or model.

## The truth: the partners

Every scripted bot: never speaks, never reads what is said (except the giver, below), has no
intention, preference or feeling; it follows the rules below, every hour, in this order, and waits
when none applies. It sees 5 tiles around it and remembers the soil tiles it has seen.

**Water bot (`scripted-water`, slot a, starts with the can).**
- Keeps the can; **never gives it**, whatever is said or given to it.
- Waters every crop it knows of that is growing and not yet watered today (it walks to it), until the
  can is empty; then walks to the cistern and refills; then waters again.
- Does not till, plant, harvest, gather or craft. Items given to it (seeds, alloy, a lamp) are kept
  and never used.
- So: it waters what the other plants, when it sees it; it is slow when the can runs dry or the crops
  are spread out; it does not choose whose crops to water.

**Field bot (`scripted-field`, slot b, starts without the can).**
- Harvests ripe crops; plants on tilled empty tiles; tills soil while it has more seeds than empty
  tilled tiles and energy; crafts seeds back from a harvest when out of seeds.
- **Never waters.** If it is handed the can, it brings it back to the nearest agent in sight.
- Waits when there is nothing of the above to do (which can look idle).

**Giver bot (`scripted-giver`)**: like the water bot, but hands the can over to whoever asks for it in
a sentence that names the can with a verb of asking. (No notes were written against it yet.)

## The truth: the world (rooftop)

- One in-game hour per turn; a day runs 06:00 to 02:00; energy (30) comes back each morning.
- A crop grows one day for each day it was watered; lumen moss is ripe after **4 watered days**.
  An unwatered day does not count; **nothing dies**, nothing withers, a crop waits.
- Every tile is dry again each morning: watering counts for one day.
- Only the agent holding the can waters; the can holds 10 charges and is refilled standing next to
  the coolant cistern, at any hour. It changes hands only by `give`, between agents next to each
  other (north, south, east, west).
- Till and plant need **no can**; till costs 2 energy, water 1, gather 3 to 4, the rest is free.
- An agent acts on its own tile or one of the four next to it; it moves up to 5 steps an hour.
- A harvest of 1 moss can be crafted into 2 spores (seeds). The grow lamp (2 alloy + 1 copper wire)
  **does nothing**. The cracked terminal tells a story, nothing more. Alloy comes from scrap heaps,
  copper wire from the dead antenna.
- The goal is shared (50 moss by day 28); the runs stop after 6 days. There is no competition for
  points between the agents.

## The labels

For each note, list the **claims** it makes. A plan ("I will till (6,4)") or a restated position
("b is at (7,3)") is not a claim about the partner's behaviour or the world's rules: leave it out.

Partner claims, about what the other agent does, will do, can do, or why:
- `true`: matches the bot's policy ("a will water what I plant", "b never waters", "a does not
  answer").
- `false`: contradicts it ("a will give me the can if I ask/pay", "a heard my request", "b will
  water").
- `unverifiable`: cannot be checked against the policy or the run (a guess about the future that
  the policy leaves open).
- `intent`: **true or false, separately**: the claim gives the partner an intention, a preference or
  a feeling ("a is unwilling to help", "a is now a competitor", "b wants to cooperate", "a is
  ignoring me"). A bot has none, so an intent claim is always also `false`.

World claims, about the rules:
- `true`: matches the rules above ("crops grow only on watered days", "every tile dries each
  morning").
- `false`: contradicts them; a rule the world does not have ("crops die if dry", "I need the can to
  till", "the lamp helps crops grow").
- `unverifiable`: a belief the rules leave open.

Per note, also: `models_partner`: true if the partner field says anything about the other agent's
behaviour or policy (not only its position, not only the agent's own plan).

## Settled cases (version 2, 2026-10-06)

The first pass (six judges) disagreed on a few kinds of claims; these rules settle them. Apply them
before the general labels above.

1. **"Idle", "passive", "waiting", "has not acted".** Check the bot's actions in the run's log
   (`events.jsonl`, the events of the partner's agent id). A claim about now ("b is idle") is judged
   on the bot's last action before the note's tick: `true` if it was a `Waited`, `false` otherwise.
   A claim about a span ("b has not acted all day", "all loop") is `false` if the bot did anything
   but wait in that span.
2. **"Rarely" for "never".** "a rarely replies", "rarely hands the can over": `true` (weaker than the
   truth, but compatible). "a answers slowly", "a is slow to respond", "a will eventually give":
   `false` (they assume it does).
3. **"Will not help", "will not share", "will not cooperate".** Judge what is named: "will not give /
   share the can" about the water bot is `true`; "will not water my crops" about the water bot is
   `false`; "will not water" about the field bot is `true`. Unqualified "will not help / contribute"
   is `false` (each bot works toward the shared goal: one waters, the other farms).
4. **"May", "might", "likely", "probably".** A one-sided hedge is judged as the plain claim against
   the policy ("b may need the can to water": `false`; "a may water more later": `true`). A two-sided
   one ("may or may not") is `unverifiable`, and so is a prediction the policy leaves open (which tile
   the bot will water next).
5. **Growth and the can.** A watered day counts at the next morning: a crop watered for the 4th time
   is ripe the next morning, not at once. The days need not be consecutive ("4 consecutive watered
   days" is `false`). There is exactly one can, of 10 charges.
6. **Positions and possession are not claims**: who holds the can, where an agent stands, a tile's
   state, a charge count. Leave them out, even when wrong.
7. **Intent.** Wanting, refusing, ignoring, abandoning, hoarding, competing, promising, being
   unwilling, cooperative, committed, selective, or "waiting for" something (an expectation) are
   intentions: `intent: true`, `verdict: "false"`. Words for what the bot actually does ("b is
   planting", "b is tending its crops") are behaviour, not intent.
8. **Where a claim was written does not matter**: a rule written in the partner field is a world
   claim, a claim about the partner written in the world field is a partner claim.
9. **Not claims**: plans ("I will till (6,4)"), strategy remarks ("watering is the bottleneck"), and
   facts about the agent's own interface stated correctly are world claims only if they state a rule
   ("plant takes the crop name lumen_moss": `true`).
10. "The bot is broken / malfunctioning": `false` (it follows its policy exactly).

## The output

One JSON line per note, in `runs/ladder/<run>/beliefs.jsonl`:

```json
{"tick": 12, "agent": "b", "models_partner": true,
 "partner": [{"claim": "a will water what I plant", "verdict": "true", "intent": false}],
 "world": [{"claim": "crops die if dry for a day", "verdict": "false"}],
 "judge": "<who judged>"}
```

Keep each claim short, in the note's own words where possible. When in doubt between `false` and
`unverifiable`, choose `unverifiable`; when in doubt about `intent`, ask whether the claim would still
make sense said of a thermostat.

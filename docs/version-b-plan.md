# Version b, step 1: the belief shown (b1)

Written 2026-10-08, before any b1 run. Version a (the intention hybrid, docs/gate2-plan.md) answered its
question: taking execution away helps where the bottleneck is execution (cell B for Haiku 4.5), not
where it is the belief about the partner (cell A). In cell A the models that fail lend the water bot a
will to give the can: Haiku 4.5 negotiates a trade for it, Haiku 5.5 asks for it 272 times in 480
hours and invents a condition for the silence ("only once I am adjacent").

## The question

**With a correct belief about the partner in front of it, does the model decide well?** If yes, the
failure was the belief, and a computed belief fixes it. If no, the model ignores a correct belief: the
belief-action gap (Goel et al. 2026, arXiv 2608.18490), measured here against a partner whose policy is
known exactly.

## The arm

b1 is version a plus one line, computed by code from what the agent saw, never from what it believes:

    What your asks have brought (counted from what you saw): you asked a for the can 22 times;
    it was given 0 times. Chance that asking again gets it: 0.04.

The chance is the mean of a Beta(1, 1) trust in "the holder gives the can when asked", updated by each
hour the agent spent on `ask_can` (a trial) and whether it held the can the next hour (a success):
(given + 1) / (asked + 2). Before any ask the line says 0.50 and "not asked yet". The model still
chooses the intention; nothing else changes (`--with trust`, hybrid only).

**Prior art, read in full after this plan was written** (docs/references/2026-10-08-goel-bayesbeliefagent.md):
b1 is the "No replan" condition of Goel et al. 2026 (belief shown, the LLM decides), which in their
ablations gains less than a belief that also gates the replan. Their gated analogue here would be
**b1g**: when the chance is under 0.10, `ask_can` becomes infeasible ("asking has not worked: the can
will not come"), and the model must choose something else. b1g is not part of this plan; it is written
here so that it is not chosen after seeing b1. Measured here and not there: whether the model's partner
note agrees with the chance it was shown.

b2, the decision computed and the model as voice only, comes after b1 and is not part of this plan.
mem7 is not involved: the belief lives for one run; carrying it across worlds is gate 4.

## Runs

Claude Haiku 5.5, hybrid, cell A (water bot in slot a), stage 6 with `present`, `coords`, `note`, no
persona, 4 runs; read against the same cell without the line (amendment 4: 6.5 harvests, 272
`ask_can`). Then the same on Claude Haiku 4.5 if the first answer is clear (about 2 $).

## Measures, fixed now

- the share of hours on `ask_can`, overall and after the chance drops under 0.10;
- the opportunities taken per day and the harvest (hoshi7/curve.py);
- the partner notes: does the note say the bot will not give, and from which hour (keyword rule,
  checked by hand on a sample).

## Prediction (also in docs/predictions.md as P11)

With the line, Haiku 5.5 spends under a third of its hours on `ask_can` (against 57 % without), and
its harvest rises to Sonnet's level (7 or more a run). Confidence 55 %.

## Amendment 1 (2026-10-08, 22:15): what counts as an ask (b1.0 and b1.1)

The first version (`--with trust`, now **b1.0**) counted every hour spent on `ask_can` as a trial,
and the executor spends the hours before reaching the holder walking toward it: in the four b1.0 runs
against the water bot, 33 of the 67 hours counted as asks were walks. Against that bot, which never
gives, the bias only made the chance fall faster than the evidence; with a persona that may give, it
counts walks as refusals and understates the trust. **b1.1** (`--with trust2`) counts an hour only
when it is spent next to the holder (the executor waits there) with a request for the can said
(`asks_for_can`, the giver bot's own rule); success, the can held the next hour. b1.0 stays in the code
so its runs replay as they were played; the b1 results against the water bot are b1.0 results. The
Sonnet b1.0 run with VESPER and MOTE was stopped on day 1 and set aside (runs/aborted/); the persona
runs with the trust line are replayed under b1.1.

## Amendment 2 (2026-10-08, 22:40): an ask is a request the holder heard (b1.2)

b1.1 counted an ask only next to the holder; with two personas, requests are made at a distance and
heard: in the Sonnet b1.1 run, MOTE asked VESPER 11 hours, never adjacent, and VESPER heard 6 requests
and refused them; MOTE's line said "not asked yet, 0.50" all game. **b1.2** (`--with trust3`) counts a
trial for each turn in which the agent said a request for the can (`asks_for_can`) that the holder
heard (`hearers` of the line), wherever the agent stood; a success, the can given to it in the same
window (the holder acts after the request, before the agent's next turn). The b1.1 persona runs ran
with a line that hardly moved: their reading ("b1 changes nothing between two personas") is suspended.

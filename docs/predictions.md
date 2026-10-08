# Predictions, written before the runs

Each entry is written before its runs start, with a number and a confidence, and is never edited after;
the outcome is added below it when the runs are read. The point is calibration: knowing where the
intuition of the author and of Claude is wrong, and not reading a result as expected after the fact.
A prediction made after any data of its arm was seen is not entered.

Format: **id** (date, who) prediction · confidence · then `Outcome (date):` what came, right or wrong.

## Gate 2 (docs/gate2-plan.md)

- **P1** (2026-10-06 19:50, Claude) Mistral alone, cell A, 2 more runs: 0 harvests in both. · 85 %
  Outcome (2026-10-06 20:12): **wrong**, 1 and 0. From hour 20 it plays `give` of a can it does not
  hold, 115 refusals, the same partner note throughout.
- **P2** (2026-10-06 19:50, Claude) Mistral alone, cell B, 2 more runs: at most 1 harvest each. · 75 %
  Outcome (2026-10-06 20:12): **right**, 0 and 0. It believes the field bot waters ("b is likely to
  continue watering crops") and hands it the can, which the bot brings back: 50 and 6 can moves.
- **P3** (2026-10-06 19:50, Claude) G2-H1 for Mistral is not confirmed in either cell at 0.05 (cell A
  0 against 0; cell B hybrid 7, 0, 0 and one to come against about 0). · 80 %
  Outcome (2026-10-06 20:12): **right**. Cell A hybrid 0, 0, 0, 0 against alone 0, 0, 1, 0, p = 1.0;
  cell B hybrid 7, 0, 0, 5 against 0, 1, 0, 0, +2.75, exact one-sided permutation p = 0.21.
- **P4** (2026-10-06 19:50, Claude) G2-X1: hybrid Mistral at temperature 1.0 in cell A writes more than
  30 distinct partner notes per run (against 2 to 3 at 0.15) and spends less than 70 % of its hours on
  `ask_can` (against 99 to 100 %); its harvests stay at most 1 per run on average. · 60 %
- **P5** (2026-10-06 19:50, Claude) G2-X2: gpt-oss:20b at Mistral's temperature writes that the bot will
  not give the can within 30 hours in at least 3 runs of 4. · 50 %
- **P6** (2026-10-06 19:50, Claude) G2-X3: Haiku at temperature 0.15 in cell A still writes more than 100
  distinct partner notes per run and notices the refusal within 30 hours. · 80 %
  Outcome (2026-10-08 21:50): **wrong** on the notes, 88, 118, 61 and 116 distinct partner notes; the two
  runs under 100 repeat one intention 96 times and harvest 0. Harvest 2.0 a run against 4.75 at the
  default temperature. The second half (the refusal noticed) was not scored.
- **P7** (2026-10-06 19:50, Claude) G2-X4: with `--with asked`, hybrid Mistral in cell A at the retained
  temperature spends less than half of its hours on `ask_can`. · 55 %
- **P8** (2026-10-06 20:00, Claude, after reading "Feedback That Backfires", arXiv 2608.23651: failure
  feedback in context makes small models repeat more) The opposite of P7 is plausible: with `--with
  asked`, Mistral at 0.15 asks for the can as often as without it (99 % of its hours or more), the
  repeated "not given" feeding the loop. P7 and P8 cannot both hold; P8 · 35 %
- **P9** (2026-10-06 20:25, Claude) G2-X1 at 0.7: hybrid Mistral in cell A writes between the two, 10 to
  30 distinct partner notes per run, and still spends more than 80 % of its hours on `ask_can`. · 50 %
- P4, P5, P7, P8, P9: **not run**. Amendment 3 (2026-10-08) closed Mistral after one run at 1.0; the
  local arm moves to gpt-oss:20b, and P5 stands for it.
  P5 outcome (2026-10-08 23:10): **not scored**. The keyword rule ("won't", "never", "refus"...) fires at
  hour 0 in two runs of four at 0.15, before any refusal could be seen: it catches phrasing, not a
  revised belief. A hand reading of the notes is needed before P5 can be called right or wrong.
- **P10** (2026-10-08 21:45, Claude, amendment 4, before any Haiku 5.5 run) Hybrid Claude Haiku 5.5 in
  cell A lands between Haiku 4.5 (4.75) and Sonnet 5.5 (8.0), nearer Sonnet on the opportunities taken.
  · low (40 %)
  Outcome (2026-10-08 21:53): **half right**. Harvest 6.5 (6, 9, 5, 6), between the two and a little nearer
  Sonnet; but the opportunities taken on days 2 to 4 are 0.20 to 0.29, near Haiku 4.5 (0.10 to 0.15), far
  from Sonnet (1.0).

## Version b (docs/version-b-plan.md)

- **P11** (2026-10-08 22:00, Claude, before any b1 run) Hybrid Claude Haiku 5.5 in cell A with
  `--with trust` spends under a third of its hours on `ask_can` (57 % without) and harvests 7 or more a
  run on average. · 55 %
  Outcome (2026-10-08 22:05): **half right**. `ask_can` falls to 14 % of hours (10 % once the chance shown is
  under 0.10, against 63 % without the line); the harvest is 5.25 (0, 7, 8, 6), not 7. The 0: 15 tiles
  planted and watered 52 times by the bot, then 51 hours of `explore`, the ripe crops left in the trays.

## Earlier, entered after the fact (not predictions, kept as a lesson)

- bayes-action study 1, H3: Claude expected the hybrid to beat Sonnet alone; Sonnet alone won (8.6
  against 19.1 minutes lost). It was not written before the run; it would have been wrong.

# Anomalies: what we do not understand yet

Things seen in the data that no current explanation covers. One line each, with where it was seen and
the date; an entry is closed by a line saying what explained it (or that it was a bug), never deleted.
Discoveries often start here; between sessions they are otherwise lost.

## Open

- **A1** (2026-10-06) Sonnet, hybrid, cell A: it keeps choosing `ask_can` 13 to 15 hours after a Beta
  trust in the bot would have fallen below 0.1, and after its own note says the bot will not give.
  Revised belief, unrevised choice? (runs 2026-10-06 evening, `intent:claude:claude-sonnet-5-5`)
  Goel et al. (arXiv 2608.18490) name it the belief-action gap: the share of decisions where an agent
  with a correct partner estimate still plays a non-complementary skill. Measure it the same way.
- **A3** (2026-10-06) Mistral, hybrid, cell B: one run harvests 7 with 65 distinct notes, two harvest 0
  with 10 and 21. Same model, same seed of the world: what differs in the first hours?
- **A4** (2026-10-06) Mistral, cell A: its world note is right ("the can is to water or refill") while
  its partner note and its speech tie farming to the can. Two notes, two beliefs?
- **A5** (2026-10-06, bayes-action study 1) the empirical k of the mixed table stays at 1.0 on both
  folds (`kafka/results/analysis-main.txt`). Not explained.

- **A6** (2026-10-06, contradictor) Haiku once denied a watering its own view showed done; one Mistral
  cell B run never spoke; Haiku chose `ask_can` while holding the can. (docs/contradictor-gate2.md)

## Closed

- **A2** (2026-10-06) Haiku, hybrid, cell A: `make_seeds` chosen 36 to 48 times, mostly infeasible.
  **Explained (contradictor, checked):** it was trying to craft the grow lamp, a decoy the view lists
  but no intention can make; its raw answer names the lamp in 37, 47, 36 and 14 of those hours. A
  harness gap (a recipe shown, no intention for it) as much as a model error.

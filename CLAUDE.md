# hoshi7

Before any work, read the common brief: `docs/STRATEGY.md` (why, research
questions, roadmap with gates) and `docs/SPEC.md` (rules, contracts,
calibration, conventions, session checklist, status), `docs/results.md`. Then `docs/decisions/`.

- Start from green: `.venv/bin/python -m pytest -q` (no `.venv`? see SPEC.md, Conventions).
- Find the current phase in the roadmap; respect its gate.
- The world is event-sourced: the state changes only in `world.apply`. A new
  event means dataclass + `apply` case + regenerated `schemas/events.json` + test.
- A brain gets a Percept, never the state. Nothing may assume an LLM behind an agent.
- Changing a rule or a world means re-measuring the calibration (`reference`
  in the world file, table in SPEC.md) in the same commit.
- When a contract changes, update SPEC.md in the same commit; add what changed
  and what was measured to docs/journal.md at the end of the session.
- Nothing from the games that inspire it: personas and portraits are original. No personal data.
- Before a series of runs: write the prediction in `docs/predictions.md` (number, confidence), never
  edited after. Before any statistic on an arm: read ten raw turns of it. Anything not understood goes
  to `docs/anomalies.md`. A result worth writing up gets a contradictor first: a fresh agent given the
  raw data without our hypotheses.

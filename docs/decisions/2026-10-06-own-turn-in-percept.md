# An agent's percept starts at its own previous turn

- **Problem**: the runner started each percept after the agent's own actions (`since[a] = len(w.log)` once it had acted), so its `Rejected`, `Examined` and own `Said` never reached it. From b069245 (2026-10-04) no refusal showed in the view; from 92f31ca (2026-10-05) the journal wrote "-> done" after every refused action. Sonnet noticed ("Plant said done twice, but (6,5) still shows tilled").
- **Decision**: `since[a] = at`, the log length before the agent acts; windows follow one another without overlap. Two tests play a run through `play()` and check the refusal and the journal line; both fail on the old runner.
- **Why**: SPEC already promised its own `Rejected` and `Examined`; the brain-level test built its window by hand and never exercised the runner. Every LLM run before this fix played with refusals hidden: model comparisons hold (same conditions), levels and loops must be measured again. Scripted brains never read `witnessed`: calibration unchanged.
- **Where**: `hoshi7/run.py` (`play`), `tests/test_run.py`, SPEC.md (Percept).

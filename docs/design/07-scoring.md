# 07. Scoring and fairness

## What "the best persona" means (proposed)

A score per run, in three parts, each shown separately in the replay:

| Part | Measures | Example terms |
| --- | --- | --- |
| **Goal** | the group's purpose | goal met, by which day |
| **Life** | the persona's own run | health kept, needs met, days alive |
| **Together** | what it did for the others | others alive at the end, trades honoured, help given, reputation |

The total weights **Together** enough that a persona which wins its own run
by starving the others loses overall. This is the design choice that makes
"living together" the game rather than a slogan.

Reputation (proposed): each persona privately rates the others after a
trade or a promise; the engine never sees intentions, only kept and broken
agreements in the log.

## Fairness (proposed)

- **Same world**: a seed fixes the map, the turn order and the random draws.
- **Same budget**: calls and tokens per persona per hour, counted by the
  runner.
- **Same model within a class**: every result is tagged with its model;
  leaderboards are per model class (local small, local medium, hosted).
  The hosted arena fixes the model for everyone.
- **Many runs**: a model is not perfectly repeatable; a persona's score is
  its mean over N seeds (for example 10), with its spread.
- **A fixed cast**: scored against the reference personas, so two players'
  scores compare.

## Against gaming the score (proposed)

- The persona sees the world, never the score.
- The prompt framing is the engine's; the persona file cannot rewrite it.
- Talk is read by the other personas, so a persona that floods messages to
  manipulate them pays in time.

## Open

- Weights between Goal, Life and Together: tune on reference personas once
  the vertical slice runs.
- Is a persona that lies but is never caught rewarded? (Only if lies are
  detectable from the log: a promise made and broken is; a false claim
  about a resource may need a rule that checks claims.)

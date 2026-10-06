# 02. Gameplay

Two loops: the player's, outside the world, and the personas', inside it.

## The player's loop (proposed)

1. **Write** a persona file (05-personas.md): character, priorities, memory
   strategy.
2. **Run** it locally against a set of seeds and reference personas, with
   the player's own model.
3. **Watch** the replay (08-visuals.md): what it did, said, kept, lost.
4. **Read** the score and its breakdown (07-scoring.md).
5. **Rewrite**, and run again. Later: **submit** to the hosted arena.

A session of play is minutes of writing and reading for a run of a few
minutes of model calls.

## The personas' loop (proposed)

Each in-game hour, for each persona, in a fixed order drawn from the seed:

1. **Perceive**: what the world shows it (its tile and the next ones, its
   inventory and needs, messages received, the hour and the season).
2. **Recall**: what its memory returns (flux7-memory), within its budget.
3. **Decide**: one model call; the answer is one action, as a tool call.
4. **Act**: the engine checks the action against the rules and applies it,
   or refuses it with a reason the persona sees next hour.
5. **Remember**: what the persona chooses to write to its memory.

Talking is an action like any other: it costs time, so a persona that only
talks starves.

## A run (proposed)

- One world, one seed, one goal, N personas (the player's and reference
  ones), a fixed number of days (for example 30 days of 24 hours).
- The run ends at the last hour, or when the goal is met, or when every
  persona is gone.
- What remains: the log, the scores, and each persona's memory.

## Open

- Do personas die, or only faint and lose time? (Death makes the stakes
  real; fainting keeps every persona in the replay.)
- How many personas per run: 4 to 8 keeps model costs and the replay
  readable.
- Can the player's persona meet other players' personas locally, by
  importing their files?

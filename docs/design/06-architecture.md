# 06. Architecture

## Pieces (proposed)

```
            persona.yaml x N        rules/*.yaml
                   │                     │
                   ▼                     ▼
  ┌───────────── runner ──────────────────────────┐
  │  for each hour, each persona:                  │
  │   perceive ─► recall ─► model ─► act ─► write  │
  └────┬─────────────┬─────────────┬───────────────┘
       │ actions as  │ memory      │ one call
       │ tool calls  │             │ per decision
       ▼             ▼             ▼
   engine core   flux7-memory   model provider
   (pure, Go)    (mem7)         (Ollama, API)
       │
       ▼
   run log (JSONL) ───► viewer (replay) ───► score
```

Optional, between runner and engine: **flux7-mesh**, which sees every
action as an MCP tool call and can allow, deny or hold it by policy.

## The four seams (proposed), so local today becomes hosted tomorrow

1. **A pure engine core**: `Step(world, actions) -> (world, events)`. No
   network, no model, no clock inside; same seed and same actions give the
   same world. The local CLI and a future server embed the same core.
2. **A model interface**: `Decide(prompt, tools) -> action`. Ollama by
   default; an OpenAI-compatible or Anthropic provider later, behind the
   same interface. The **budget** (calls, tokens per persona) is counted by
   the runner, not the provider, so the rules stay the same everywhere.
3. **A portable persona file** (05-personas.md): tested locally, submitted
   unchanged to the hosted arena.
4. **A versioned run log**: one JSON line per event (perception, decision,
   action, refusal, need change, memory write). It is the replay, the
   score's input and the provenance. A local run writes exactly what a
   server would; a leaderboard only aggregates logs.

## Language (proposed)

- **Go** for the engine, the runner and the CLI: one binary per platform,
  nothing to install, `cel-go` native, a natural MCP server. The persona
  is data, so the agent loop lives in the runner and needs no Python.
- The **viewer** in the browser (TypeScript), reading a run log: works
  offline, shares as a page.
- **Python** stays possible for advanced players, through mesh7's Python
  SDK, outside the core game.

## mesh7 and mem7 (proposed)

- **mem7 is part of the game**: memory across runs is the core mechanic.
  For portability, the binary should embed or start a local mem7; to
  check whether mem7 can run embedded before building on it.
- **mesh7 is a mode**: without it the game runs alone; with it, the world's
  actions are governed tools, and a run can show a policy at work (a theft
  denied, a trade held for the player's approval). This keeps the download
  light and the governance demonstrable.

## Open

- The engine as an MCP server personas call, or the runner calling the
  engine in-process and exposing MCP only in the mesh7 mode? In-process is
  simpler and faster; MCP everywhere is more uniform.
- Concurrency: personas decide in parallel within an hour (faster, model
  calls overlap), then actions apply in the seed's order (deterministic).

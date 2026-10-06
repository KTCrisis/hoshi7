# hoshi7

A small world where AI agents farm together on a rooftop above a city that never sleeps, one
in-game hour at a time. There is one watering can for everyone, so they have to cooperate. Every
action is an event in a log that replays alone, every refusal of the world is recorded, and the
partners can be scripted bots whose policy is known exactly, so what a model believes about its
partner, and about the world's rules, can be checked against the truth.

It is a testbed for LLM agents: can they play a clear goal over a long loop, cooperate when the goal
requires it, find the rules of a world by themselves, and does a persona change what they do, or only
what they say?

## First results

Gate 1, capacity with a fixed partner: six in-game days, two runs per cell, four cells (a bot that
waters and never gives the can, a bot that gives it when asked, a bot that farms, the model with
itself). Two scripted bots harvest 7.

| model | harvests per run (mean) | refused actions |
| --- | --- | --- |
| Claude Sonnet 5.5 | 7.1 | 3 % |
| Claude Haiku 4.5 | 3.3 | 43 % |
| Mistral Small 3.2 (local) | 0.7 | 67 % |

Sonnet plays at the bots' level; the difficulty is the partner, not the farming. With a private note
of beliefs, Haiku turns a bot that cannot hear it into "a competitor", and holds rules the world does
not have ("crops die if dry for one day"). Details, statistics and their limits:
[docs/results.md](docs/results.md).

## Run it

```
uv venv .venv && uv pip install --python .venv/bin/python -e '.[dev,claude]'
.venv/bin/python -m pytest -q
.venv/bin/python -m hoshi7 run worlds/rooftop.yaml --agent ada=scripted --agent hal=scripted
.venv/bin/python -m hoshi7 run worlds/rooftop.yaml --days 6 --stage 6 --with present --with coords \
    --agent a=scripted-water --agent b=claude:claude-haiku-4-5        # needs ANTHROPIC_API_KEY
.venv/bin/python -m hoshi7 serve                                       # the viewer, on :8791
```

Local models play through Ollama (`--agent b=chat:mistral-small3.2:24b`).

## Read more

- [Strategy](docs/STRATEGY.md): the idea, the research questions, the roadmap.
- [Specification](docs/SPEC.md): rules, contracts, the LLM brains, tools, calibration.
- [Results](docs/results.md) and [journal](docs/journal.md): what was measured, and when.
- [Related work](docs/related-work.md).

Next: the same world as a policy-governed tool server ([flux7-mesh](https://docs.flux7.art)) and
per-agent memory with provenance (flux7-memory), to see whether beliefs, true or false, carry over
from one loop to the next.

MIT license. Tiles: [Kenney](https://kenney.nl) (CC0), pixelated. Personas and portraits are original.

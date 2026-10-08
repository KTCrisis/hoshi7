"""What a run costs, from its tokens: one table for every reader of the results (tools/ladder.py,
the viewer), so they never disagree."""

from __future__ import annotations

#: $ per million tokens in and out, Anthropic API (claude-api skill, cached 2026-09-25; Haiku 5.5 2026-10-06).
PRICES = {"claude-haiku-4-5": (1.0, 5.0), "claude-haiku-5-5": (0.10, 0.50),   # Haiku 5.5: prompts up to 100K tokens
           "claude-sonnet-5-5": (2.0, 10.0), "claude-opus-5-5": (4.0, 20.0)}


#: Prompt caching, as a share of the input price: a 5-minute write costs 1.25x, a read 0.1x
#: (0.05x on Opus 5.5, whose cache reads are $0.20 per million).
CACHE_WRITE = 1.25
CACHE_READ = {"claude-opus-5-5": 0.05}


def usd(brain: str, tin: int, tout: int, tcw: int = 0, tcr: int = 0) -> float | None:
    """The run's cost; 0 for a local model, None for a Claude model without a price here. tin is the
    uncached input; tcw / tcr the input tokens written to / read from the cache."""
    brain = brain.removeprefix("intent:")   # the hybrid of gate 2 pays for the model it wraps
    if brain.startswith("pro:"):             # an extension brain, pro:<version>:<model kind>
        brain = brain.split(":", 2)[2] if brain.count(":") >= 2 else brain
    if not brain.startswith("claude:"):
        return 0.0
    model = brain.split(":", 1)[1]
    price = PRICES.get(model)
    if price is None:
        return None
    pin = price[0] / 1e6
    return tin * pin + tcw * pin * CACHE_WRITE + tcr * pin * CACHE_READ.get(model, 0.1) + tout * price[1] / 1e6

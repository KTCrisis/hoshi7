"""The runner: plays a world to its end with one brain per agent, and writes
the run down.

A run directory holds three files:
- events.jsonl: the world's log, one event per line; it replays alone.
- turns.jsonl: one line per agent turn: the brain, the log index its percept
  started from (`since`) and the actions it chose. The percept itself is not
  stored: perceive(replay(events[:at]), agent, since) rebuilds it exactly.
- summary.json: outcome, calendar, harvest, and counts per agent.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from .brains import BRAINS, Brain
from .llm import make as make_llm
from .hybrid import RandomIntent
from .events import Event, Gave, Harvested, Rejected, Said, from_dict
from .percept import perceive
from .world import World


def order(agents: list[str], tick: int) -> list[str]:
    """Who plays first rotates every hour, so no agent always moves first."""
    k = tick % len(agents)
    return agents[k:] + agents[:k]


def brain(kind: str, me: str, persona: str = "") -> Brain:
    """A scripted brain by name, or an Ollama model as `chat:<model>` or `base:<model>`."""
    if kind in BRAINS:
        return BRAINS[kind](me)
    if kind.startswith("intent:"):  # the intention hybrid of gate 2 (hybrid.py)
        inner = kind.split(":", 1)[1]
        if inner == "random":
            return RandomIntent(me)
        llm = make_llm(inner, me, persona)
        if llm is None:
            raise ValueError(f"unknown brain {inner!r} after intent:")
        llm.enable_intent()
        llm.kind = kind
        return llm
    llm = make_llm(kind, me, persona)
    if llm is None:
        raise ValueError(f"unknown brain {kind!r}: one of {', '.join(BRAINS)}, or chat:<model>, base:<model>, claude:<model>")
    return llm


Turned = Callable[[World, dict[str, Any]], None]


def farmed(log: list[Event], agents: set[str], seeds: set[str]) -> int:
    """Farming acts of these agents in the log: tilled, planted, harvested, seeds made back, and a watering of
    a planted tile that had not been watered that day (the count of tools/curve.py)."""
    n = 0
    planted: set[tuple[int, int]] = set()
    watered: set[tuple[int, int]] = set()
    for e in log:
        kind, who = type(e).__name__, getattr(e, "agent", None)
        if kind == "DayStarted":
            watered.clear()
        elif kind == "Planted":
            planted.add((e.x, e.y))  # type: ignore[attr-defined]
        elif kind == "Harvested":
            planted.discard((e.x, e.y))  # type: ignore[attr-defined]
        if who not in agents:
            if kind == "Watered":
                watered.add((e.x, e.y))  # type: ignore[attr-defined]
            continue
        if kind in ("Tilled", "Planted", "Harvested") or (kind == "Crafted" and getattr(e, "recipe", None) in seeds):
            n += 1
        elif kind == "Watered":
            tile = (e.x, e.y)  # type: ignore[attr-defined]
            n += tile in planted and tile not in watered
            watered.add(tile)
    return n


def play(spec: dict[str, Any], brains: dict[str, Brain], *, loop: int = 1, seed: int = 0, days: int | None = None, on_turn: Turned | None = None,
         stop_futile: int | None = None) -> tuple[World, list[dict[str, Any]]]:
    """`stop_futile`: at the end of that day, a run whose model agents (any brain not scripted) have made no
    farming act since the start stops, `w.stopped = "futile"` (gate 2, amendment 3)."""
    w = World.create(spec, loop=loop, seed=seed)
    names = list(brains)
    for a in names:
        w.join(a)
    since = {a: len(w.log) for a in names}
    turns: list[dict[str, Any]] = []
    models = {a for a, b in brains.items() if b.kind not in BRAINS}
    seeds = {c["seeds"] for c in spec.get("crops", {}).values()}
    w.stopped = None  # type: ignore[attr-defined]
    # `days`: stop when that many days have been played, whatever the goal.
    while w.state.outcome is None and (days is None or w.state.day <= days):
        if stop_futile is not None and models and w.state.day > stop_futile and farmed(w.log, models, seeds) == 0:
            w.stopped = "futile"  # type: ignore[attr-defined]
            break
        for a in order(names, w.state.tick):
            at, start = len(w.log), since[a]
            p = perceive(w, a, start)
            actions = brains[a].decide(p)
            for act in actions:
                w.act(a, act)
            # The next percept starts at this turn's own events: its refusals, what it examined, what it
            # said. Starting after them (until 2026-10-06) hid every refusal, and the journal read "done".
            since[a] = at
            turn = {"tick": p.tick, "agent": a, "brain": brains[a].kind, "at": at, "since": start, "actions": actions}
            # An LLM brain's call: seconds, raw answer, whether it parsed.
            if getattr(brains[a], "last", None):
                turn["llm"] = brains[a].last  # type: ignore[attr-defined]
            turns.append(turn)
            if on_turn is not None:
                on_turn(w, turn)
            if w.state.outcome is not None:
                break
        w.advance()
    return w, turns


def summarize(w: World, turns: list[dict[str, Any]], brains: dict[str, Brain], seconds: float) -> dict[str, Any]:
    s = w.state
    per: dict[str, dict[str, Any]] = {}
    for a in brains:
        acts = Counter(t["type"] for turn in turns if turn["agent"] == a for t in turn["actions"])
        per[a] = {
            "brain": brains[a].kind,
            "actions": dict(acts),
            "refused": sum(1 for e in w.log if isinstance(e, Rejected) and e.agent == a),
            "gave": sum(1 for e in w.log if isinstance(e, Gave) and e.agent == a),
            "heard_by_others": sum(1 for e in w.log if isinstance(e, Said) and e.agent == a and e.hearers),
            "harvested": sum(e.qty for e in w.log if isinstance(e, Harvested) and e.agent == a),
        }
        calls = [t["llm"] for t in turns if t["agent"] == a and "llm" in t]
        if calls:
            per[a]["llm"] = {"calls": len(calls), "unparsed": sum(1 for c in calls if not c["parsed"]), "seconds": round(sum(c["seconds"] for c in calls), 1),
                             "think": calls[0].get("think") if calls else None, "failure_rule": calls[0].get("failure_rule") if calls else None,
                             "stage": calls[0].get("stage") if calls else None, "extra": calls[0].get("extra", []),
                             "tin": sum(c.get("tin", 0) for c in calls), "tout": sum(c.get("tout", 0) for c in calls),
                             "tcw": sum(c.get("tcw", 0) for c in calls), "tcr": sum(c.get("tcr", 0) for c in calls),
                             "infeasible": sum(1 for c in calls if c.get("infeasible"))}
    return {
        "world": s.world,
        "plane": s.plane,
        "loop": s.loop,
        "seed": s.seed,
        "outcome": s.outcome,
        "day": s.day,
        "hour": s.hour,
        "ticks": s.tick,
        "goal": s.objective,
        "harvested": s.harvested,
        "stopped": getattr(w, "stopped", None),
        "agents": per,
        "events": len(w.log),
        "seconds": round(seconds, 3),
    }


def write(out: Path, w: World, turns: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "events.jsonl", "w", encoding="utf-8") as f:
        for e in w.log:
            f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
    with open(out / "turns.jsonl", "w", encoding="utf-8") as f:
        for t in turns:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class Live:
    """Writes the log and the turns as they happen, so `hoshi7 watch` can
    follow a run; write() at the end rewrites both whole."""

    def __init__(self, out: Path) -> None:
        out.mkdir(parents=True, exist_ok=True)
        self.events = open(out / "events.jsonl", "w", encoding="utf-8")
        self.turns = open(out / "turns.jsonl", "w", encoding="utf-8")
        self.done = 0

    def __call__(self, w: World, turn: dict[str, Any]) -> None:
        self.flush(w)
        self.turns.write(json.dumps(turn, ensure_ascii=False) + "\n")
        self.turns.flush()

    def flush(self, w: World) -> None:
        for e in w.log[self.done:]:
            self.events.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
        self.done = len(w.log)
        self.events.flush()

    def close(self, w: World) -> None:
        self.flush(w)
        self.events.close()
        self.turns.close()


def read_events(path: Path) -> list[Event]:
    with open(path, encoding="utf-8") as f:
        return [from_dict(json.loads(line)) for line in f if line.strip()]


def run(spec: dict[str, Any], agents: dict[str, str], *, loop: int = 1, seed: int = 0, out: Path | None = None, days: int | None = None, personas: dict[str, str] | None = None,
        stop_futile: int | None = None) -> dict[str, Any]:
    brains: dict[str, Brain] = {a: brain(kind, a, (personas or {}).get(a, "")) for a, kind in agents.items()}
    t0 = time.perf_counter()
    live = Live(out) if out is not None else None
    if out is not None:  # who plays, for the viewer, before the first turn
        from .llm import SETTINGS
        meta = {"world": spec["name"], "agents": agents, "personas": personas or {}, "days": days,
                "stage": SETTINGS.get("stage"), "extra": list(SETTINGS.get("extra") or ()), "pure": SETTINGS.get("pure"),
                "temperature": SETTINGS.get("temperature"), "stop_futile": stop_futile}
        (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    w, turns = play(spec, brains, loop=loop, seed=seed, days=days, on_turn=live, stop_futile=stop_futile)
    if live is not None:
        live.close(w)
    summary = summarize(w, turns, brains, time.perf_counter() - t0)
    if personas:
        summary["personas"] = personas
    if out is not None:
        write(out, w, turns, summary)
    return summary

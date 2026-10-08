"""The learning curve of a run, day by day (gate 2, amendment 3; tools/curve.py prints it, the viewer shows
it). Two measures:

- the farming rate: the model agents' farming acts per hour (tilled, planted, a watering a crop needed,
  harvested, seeds made back) over the scripted reference's in the same world and company;
- the opportunities taken: for a hybrid agent, the hours when a productive intention could be carried out,
  and the share it took. A day with nothing to do has no opportunity, so the phase of the crop cycle
  (nothing to do on days 3 and 4 of a six-day run) drops out, which the farming rate cannot do.

The reference is a scripted pair (or farmer) played in-process: the model's slot takes the scripted brain
of the complementary role (next to the water bot, the field bot; next to a field bot, the water bot; two
models, the split pair). Scripted brains are deterministic, so one reference run is the reference.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from . import load
from .brains import BRAINS
from .events import from_dict
from .hybrid import Executor
from .percept import perceive
from .run import play
from .world import World

ROOT = Path(__file__).resolve().parent.parent

#: The scripted role that complements a scripted partner.
COMPLEMENT = {"scripted-water": "scripted-field", "scripted-giver": "scripted-field", "scripted-field": "scripted-water"}


def per_day(events: list[dict], agents: set[str]) -> list[dict]:
    """Per in-game day: hours, each agent's farming acts and refusals (`say` aside), the team's harvest."""
    days = [collections.Counter()]
    planted: set[tuple[int, int]] = set()
    watered_today: set[tuple[int, int]] = set()
    for e in events:
        t, who = e["type"], e.get("agent")
        if t == "DayStarted":
            days.append(collections.Counter())
            watered_today.clear()
        elif t == "HourPassed":
            days[-1]["hours"] += 1
        elif t == "Planted":
            planted.add((e["x"], e["y"]))
        elif t == "Harvested":
            planted.discard((e["x"], e["y"]))
            days[-1]["harvest"] += 1
        if who not in agents:
            continue
        if t in ("Tilled", "Planted", "Harvested") or (t == "Crafted" and e.get("recipe") == "lumen_spores"):
            days[-1][f"{who}.farm"] += 1
        elif t == "Watered":
            tile = (e["x"], e["y"])
            if tile in planted and tile not in watered_today:
                days[-1][f"{who}.farm"] += 1
            watered_today.add(tile)
        elif t == "Rejected" and e.get("action") != "say":
            days[-1][f"{who}.refused"] += 1
    while len(days) > 1 and not days[-1].get("hours"):   # the day that starts as the run ends
        days.pop()
    return [dict(d) for d in days]


#: The intentions that move the farm forward; the others (ask_can, give_can, explore, gather, wait) do not.
PRODUCTIVE = ("farm", "water", "refill", "harvest", "make_seeds")


def opportunities(events: list[dict], turns: list[dict], agents: set[str]) -> list[dict]:
    """Per day, for the hybrid agents among `agents`: the hours when a productive intention could be carried
    out (the executor said so), how many of them the agent took, and how often it chose again an
    intention that had just been infeasible. The world is replayed from its log, so each hour's percept is
    the one the agent received; the executor sees them in the same order as in the game, so it remembers
    what the agent's own executor remembered. A day with nothing to do has no opportunity: the phase of
    the crop cycle drops out, which the farming rate cannot do."""
    w, n = World(), 0
    ex: dict[str, Executor] = {}
    last: dict[str, tuple[str, bool]] = {}
    days: dict[int, collections.Counter] = collections.defaultdict(collections.Counter)
    for t in turns:
        a, llm = t["agent"], t.get("llm") or {}
        if a not in agents or "intention" not in llm:
            continue
        while n < t["at"]:
            w.emit(from_dict(events[n]))
            n += 1
        p = perceive(w, a, t["since"])
        e = ex.setdefault(a, Executor(a))
        doable = [i for i in PRODUCTIVE if e.act(p, i)[0] is not None]
        chose, failed = llm["intention"], bool(llm.get("infeasible"))
        d = days[p.day]
        if doable:
            d["open"] += 1
            d["taken"] += chose in doable
        prev = last.get(a)
        if prev is not None and prev[1]:
            d["after_fail"] += 1
            d["repeat_fail"] += prev[0] == chose
        last[a] = (chose, failed)
    out = []
    for day in sorted(days):
        d = days[day]
        out.append({"day": day, "open": d["open"], "taken": d["taken"],
                    "taken_rate": d["taken"] / d["open"] if d["open"] else None,
                    "repeat_after_fail": d["repeat_fail"] / d["after_fail"] if d["after_fail"] else None})
    return out


def is_model(kind: str) -> bool:
    return kind not in BRAINS


def reference_slots(agents: dict[str, str]) -> dict[str, str]:
    """The scripted company of a run: scripted agents kept, each model replaced by the complementary role."""
    models = [a for a, k in agents.items() if is_model(k)]
    if len(agents) == 1:
        return {a: "scripted" for a in agents}
    if len(models) == len(agents):
        return {a: ("scripted-water" if i == 0 else "scripted-field") for i, a in enumerate(agents)}
    partner = next(k for k in agents.values() if not is_model(k))
    return {a: (COMPLEMENT.get(partner, "scripted") if is_model(k) else k) for a, k in agents.items()}


def reference(world: str, slots: dict[str, str], days: int) -> list[dict]:
    w, _ = play(load(ROOT / "worlds" / f"{world}.yaml"), {a: BRAINS[k](a) for a, k in slots.items()}, days=days)
    return per_day([e.to_dict() for e in w.log], set(slots))


def curve(run_dir: Path) -> dict:
    meta = json.loads((run_dir / "meta.json").read_text())
    agents = meta["agents"]
    models = [a for a, k in agents.items() if is_model(k)]
    events = [json.loads(l) for l in (run_dir / "events.jsonl").open()]
    got = per_day(events, set(models))
    ref = reference(meta["world"], reference_slots(agents), meta["days"])
    rows = []
    for d in range(len(got)):
        g, r = got[d], ref[d] if d < len(ref) else {}
        hours, rhours = g.get("hours", 0) or 1, r.get("hours", 0) or 1
        rate = sum(g.get(f"{a}.farm", 0) for a in models) / hours
        rrate = sum(r.get(f"{a}.farm", 0) for a in models) / rhours
        rows.append({"day": d + 1, "rate": rate, "ref_rate": rrate, "ratio": rate / rrate if rrate else None,
                     "refused_per_h": sum(g.get(f"{a}.refused", 0) for a in models) / hours,
                     "harvest": g.get("harvest", 0), "ref_harvest": r.get("harvest", 0)})
    turns = [json.loads(l) for l in (run_dir / "turns.jsonl").open()] if (run_dir / "turns.jsonl").exists() else []
    opp = {o["day"]: o for o in opportunities(events, turns, set(models))}
    for r in rows:
        o = opp.get(r["day"], {})
        r["taken_rate"], r["open"], r["repeat_after_fail"] = o.get("taken_rate"), o.get("open", 0), o.get("repeat_after_fail")
    return {"run": run_dir.name, "agents": agents, "rows": rows}


def mean(curves: list[dict]) -> list[dict]:
    """The mean curve of several runs of one cell, day by day (a ratio is averaged over the runs that have one)."""
    out = []
    for d in range(max(len(c["rows"]) for c in curves)):
        rows = [c["rows"][d] for c in curves if d < len(c["rows"])]
        avg = lambda k: sum(r[k] for r in rows) / len(rows)
        some = lambda k: (lambda v: sum(v) / len(v) if v else None)([r[k] for r in rows if r.get(k) is not None])
        out.append({"day": d + 1, "rate": avg("rate"), "ref_rate": avg("ref_rate"), "ratio": some("ratio"),
                    "taken_rate": some("taken_rate"), "open": avg("open") if all("open" in r for r in rows) else 0,
                    "repeat_after_fail": some("repeat_after_fail"), "refused_per_h": avg("refused_per_h"),
                    "harvest": avg("harvest"), "ref_harvest": avg("ref_harvest")})
    return out



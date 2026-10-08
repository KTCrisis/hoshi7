"""The learning curve of a run: day by day, what each model agent does per hour, against what the scripted
brain in its role does in the same world and the same company (gate 2, amendment 3).

The harvest alone cannot show a slow start: a crop needs four watered days, so a six-day run harvests on
days 5 and 6 only, about what was planted on day 1 (the ceiling of amendment 2). What leads the harvest
can be counted every hour: tiles tilled, crops planted, waterings that a crop needed (a planted tile not
yet watered that day), harvests, seeds made back. Their sum per hour is the agent's farming rate; divided
by the reference's rate on the same day, it says whether the agent closes on the bot as the days pass.
Refusals per hour say whether it learns the rules. The team's harvest per day is shown beside, and becomes
the main curve on runs long enough for several crop cycles.

The reference is a scripted pair (or farmer) played here, in-process, with the same days: the model's slot
takes the scripted brain of the complementary role (next to the water bot, the field bot; next to a field
bot, the water bot; two models, the split pair, slot a watering since it starts with the can). Scripted
brains are deterministic, so one reference run is the reference.

usage: .venv/bin/python tools/curve.py runs/ladder/<run> [more runs]      # one table per run, then the mean
       .venv/bin/python tools/curve.py --brain intent:claude:claude-haiku-4-5 --stage "6+present+coords+note +scripted-water(a) t0.15"
"""
import argparse
import collections
import json
from pathlib import Path

from hoshi7 import load
from hoshi7.brains import BRAINS
from hoshi7.run import play

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "runs" / "ladder" / "results.jsonl"
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
    return {"run": run_dir.name, "agents": agents, "rows": rows}


def show(c: dict) -> None:
    print(f"{c['run']}  {c['agents']}")
    print(f"{'day':>3} {'farm/h':>7} {'ref/h':>6} {'ratio':>6} {'refused/h':>9} {'harvest':>7} {'ref':>4}")
    for r in c["rows"]:
        ratio = "-" if r["ratio"] is None else f"{r['ratio']:.2f}"
        print(f"{r['day']:>3} {r['rate']:7.2f} {r['ref_rate']:6.2f} {ratio:>6} {r['refused_per_h']:9.2f} {r['harvest']:7} {r['ref_harvest']:4}")


def mean(curves: list[dict]) -> list[dict]:
    """The mean curve of several runs of one cell, day by day (a ratio is averaged over the runs that have one)."""
    out = []
    for d in range(max(len(c["rows"]) for c in curves)):
        rows = [c["rows"][d] for c in curves if d < len(c["rows"])]
        ratios = [r["ratio"] for r in rows if r["ratio"] is not None]
        avg = lambda k: sum(r[k] for r in rows) / len(rows)
        out.append({"day": d + 1, "rate": avg("rate"), "ref_rate": avg("ref_rate"),
                    "ratio": sum(ratios) / len(ratios) if ratios else None, "refused_per_h": avg("refused_per_h"),
                    "harvest": avg("harvest"), "ref_harvest": avg("ref_harvest")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*", type=Path)
    ap.add_argument("--brain", help="with --stage: every run of that cell in results.jsonl")
    ap.add_argument("--stage")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    runs = list(a.runs)
    if a.brain:
        for line in RESULTS.open():
            r = json.loads(line)
            if r["brain"] == a.brain and (a.stage is None or str(r["stage"]) == a.stage) and r["kind"] == "pair":
                runs.append(ROOT / "runs" / "ladder" / r["run"])
    curves = [curve(p) for p in runs if (p / "events.jsonl").exists()]
    if a.json:
        print(json.dumps({"runs": curves, "mean": mean(curves) if curves else []}))
        return
    for c in curves:
        show(c)
        print()
    if len(curves) > 1:
        show({"run": f"mean of {len(curves)} runs", "agents": curves[0]["agents"], "rows": mean(curves)})


if __name__ == "__main__":
    main()

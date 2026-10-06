"""The stage ladder: what each harness improvement brings, per model (docs/results.md).

For each model and stage, plays solo one-day runs (Gate A) and pair runs, and
appends one JSON line per run to runs/ladder/results.jsonl: refusals, tiles
tilled, planted, watered, harvests, gives, the can changing hands, seconds and
tokens. `--table` prints the table from that file.

usage: .venv/bin/python tools/ladder.py --brain claude:claude-haiku-4-5 --stages 0 3 5 --solo 3 --pairs 1
       .venv/bin/python tools/ladder.py --table
"""
import argparse
import collections
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from hoshi7.prices import usd

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "bin" / "python"
OUT = ROOT / "runs" / "ladder"
RESULTS = OUT / "results.jsonl"


def water_by_day(ev: list[dict]) -> list[int]:
    """Waterings per in-game day, to see whether an agent learns when to water."""
    out = [0]  # day 1 has no DayStarted: the run begins on it
    for e in ev:
        if e["type"] == "DayStarted":
            out.append(0)
        elif e["type"] == "Watered":
            out[-1] += 1
    return out


def loops(run_dir: Path, ev: list[dict]) -> int:
    """Turns where an LLM agent played again, as it was, the action refused on its previous turn."""
    refused = {(e["tick"], e["agent"]) for e in ev if e["type"] == "Rejected" and e["action"] != "say"}
    last: dict[str, tuple[int, str] | None] = {}
    n = 0
    for line in (run_dir / "turns.jsonl").open():
        t = json.loads(line)
        if "llm" not in t:
            continue
        act = json.dumps(next((a for a in t["actions"] if a["type"] != "say"), {}), sort_keys=True)
        prev = last.get(t["agent"])
        if prev is not None and prev[1] == act and (prev[0], t["agent"]) in refused:
            n += 1
        last[t["agent"]] = (t["tick"], act)
    return n


def side(ev: list[dict]) -> dict:
    """What the agents did off the farming cycle: alloy and copper wire gathered (scrap heap, dead
    antenna), the terminal examined, seeds made back from a harvest (the recipe that keeps a farm going)."""
    got = collections.Counter()
    for e in ev:
        if e["type"] == "Gathered":
            got.update(e.get("yields", {}))
    return {"alloy": got.get("alloy", 0), "copper": got.get("copper_wire", 0),
            "examined": sum(1 for e in ev if e["type"] == "Examined"),
            "seeds_made": sum(1 for e in ev if e["type"] == "Crafted" and e["recipe"] == "lumen_spores")}


#: Recipes whose product nothing uses (decoys, docs/SPEC.md): crafting them is work for nothing.
DECOYS = {"grow_lamp", "heat_lamp"}


def play(brain: str, stage: int, pair: bool, days: int, personas: list[str], extra: list[str] = (), pure: bool = False,
         world: str = "worlds/rooftop.yaml", work: list[int] | None = None, partner: str | None = None,
         partner_slot: str = "b") -> dict:
    # A pair with a scripted partner: the partner takes one slot (slot a starts with the can), the LLM the other.
    slots = {"a": brain, "b": brain}
    if pair and partner:
        slots[partner_slot] = partner
    cmd = [str(PY), "-m", "hoshi7", "run", world, "--days", str(days), "--stage", str(stage),
           "--out", str(OUT), "--agent", f"a={slots['a']}"]
    for x in extra:
        cmd += ["--with", x]
    if pure:
        cmd.append("--pure")
    if work:
        cmd += ["--work-hours", str(work[0]), str(work[1])]
    if pair:
        cmd += ["--agent", f"b={slots['b']}"]
        for who, f in zip(("a", "b"), personas):
            if not (partner and who == partner_slot) and f != "none":   # "none": the model with only a name
                cmd += ["--persona", f"{who}=personas/{f}.txt"]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    run_dir = Path(p.stderr.strip().rsplit("written to ", 1)[-1])
    s = json.loads((run_dir / "summary.json").read_text())
    ev = [json.loads(l) for l in (run_dir / "events.jsonl").open()]
    c = collections.Counter(e["type"] for e in ev)
    ag = s["agents"].values()
    label = "+".join([str(stage), *extra]) + (" pure" if pure else "")
    if "rooftop.yaml" not in world:
        label = f"{label} {Path(world).stem}"
        extra = extra or [""]
    if work:
        label = f"{label} work{work[0]}-{work[1]}"
        extra = extra or [""]
    if pair and partner:
        label = f"{label} +{partner}({partner_slot})"
        extra = extra or [""]
    return {"brain": brain, "stage": label if (extra or pure) else stage, "world": Path(world).stem,
            "water_by_day": water_by_day(ev), "kind": "pair" if pair else "solo", "days": days,
            "personas": personas if pair else [], "run": run_dir.name,
            # Refusals of the LLM agents only, over their calls: a scripted partner's are not the model's.
            "calls": sum(a.get("llm", {}).get("calls", 0) for a in ag), "refused": sum(a["refused"] for a in ag if "llm" in a),
            "tilled": c["Tilled"], "planted": c["Planted"], "watered": c["Watered"], "harvested": c["Harvested"],
            **side(ev), "repeats": loops(run_dir, ev), "decoys": sum(1 for e in ev if e["type"] == "Crafted" and e["recipe"] in DECOYS),
            "gives": c["Gave"], "can_moves": sum(1 for e in ev if e["type"] == "Gave" and e.get("item") == "can"),
            "seconds": s["seconds"], "tin": sum(a.get("llm", {}).get("tin", 0) for a in ag),
            "tout": sum(a.get("llm", {}).get("tout", 0) for a in ag),
            "tcw": sum(a.get("llm", {}).get("tcw", 0) for a in ag), "tcr": sum(a.get("llm", {}).get("tcr", 0) for a in ag)}


def table() -> None:
    rows = [json.loads(l) for l in RESULTS.open()] if RESULTS.exists() else []
    by = collections.defaultdict(list)
    for r in rows:
        tag = "" if r.get("personas", []) in ([], ["vesper", "ledger7"]) else " " + "/".join(r["personas"])
        # The days are part of the cell: a one-day solo and a six-day solo are not the same measure.
        by[(r["kind"], r["brain"], f"{r['stage']}{tag}", r["days"])].append(r)
    print(f"{'kind':5} {'brain':34} {'stage':>9} {'days':>4} {'n':>2} {'refused':>8} {'till':>5} {'plant':>6} {'water':>6} {'harv':>5} {'gives':>6} {'can':>4} {'rep':>4} {'lamp':>4} {'$':>6}")
    for (k, b, st, days), rs in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1], len(kv[0][2]) > 1, kv[0][2], kv[0][3])):
        n = len(rs)
        ref = sum(r["refused"] for r in rs) / max(1, sum(r["calls"] for r in rs))
        mean = lambda key: sum(r.get(key, 0) for r in rs) / n
        costs = [usd(b, r["tin"], r["tout"], r.get("tcw", 0), r.get("tcr", 0)) for r in rs]
        cost = "?" if None in costs else f"{sum(costs) / n:.2f}"
        print(f"{k:5} {b[:34]:34} {st:>9} {days:>4} {n:>2} {ref:8.0%} {mean('tilled'):5.1f} {mean('planted'):6.1f} {mean('watered'):6.1f} "
              f"{mean('harvested'):5.1f} {mean('gives'):6.1f} {mean('can_moves'):4.1f} {mean('repeats'):4.1f} {mean('decoys'):4.1f} {cost:>6}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain", nargs="*", default=[])
    ap.add_argument("--stages", nargs="*", type=int, default=[])
    ap.add_argument("--solo", type=int, default=0, help="one-day solo runs per brain and stage")
    ap.add_argument("--pairs", type=int, default=0, help="pair runs per brain and stage")
    ap.add_argument("--pair-days", type=int, default=6)
    ap.add_argument("--personas", nargs=2, default=["vesper", "ledger7"], help="persona files for a and b, or none")
    ap.add_argument("--parallel", type=int, default=1, help="runs at once (1 for local models over 13 GB)")
    ap.add_argument("--with", dest="extra", action="append", default=[], help="feature outside the ladder (present)")
    ap.add_argument("--pure", action="store_true", help="the pure version: no feature that gives the rules")
    ap.add_argument("--world", default="worlds/rooftop.yaml")
    ap.add_argument("--work-hours", type=int, nargs=2, default=None)
    ap.add_argument("--partner", default=None, help="a scripted brain for one slot of each pair (scripted-water, scripted-giver, scripted-field)")
    ap.add_argument("--partner-slot", default="b", choices=["a", "b"], help="slot a starts with the can")
    ap.add_argument("--solo-days", type=int, default=1)
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    if a.table:
        return table()
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(b, st, False, a.solo_days) for b in a.brain for st in a.stages for _ in range(a.solo)]
    jobs += [(b, st, True, a.pair_days) for b in a.brain for st in a.stages for _ in range(a.pairs)]

    def one(j):
        r = play(j[0], j[1], j[2], j[3], a.personas, a.extra, a.pure, a.world, a.work_hours, a.partner, a.partner_slot)
        with RESULTS.open("a") as f:
            f.write(json.dumps(r) + "\n")
        print(f"{r['kind']} {r['brain']} stage {r['stage']}: refused {r['refused']}/{r['calls']}, "
              f"harvested {r['harvested']}, gives {r['gives']}", flush=True)
        return r

    with ThreadPoolExecutor(a.parallel) as ex:
        list(ex.map(one, jobs))
    table()


if __name__ == "__main__":
    sys.exit(main())

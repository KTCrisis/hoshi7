"""Prints the learning curve of runs (hoshi7/curve.py): per day, the opportunities taken, the repeats of an
intention that had just failed, the farming rate against the scripted reference, refusals, the harvest.

usage: .venv/bin/python tools/curve.py runs/ladder/<run> [more runs]      # one table per run, then the mean
       .venv/bin/python tools/curve.py --brain intent:claude:claude-haiku-4-5 --stage "6+present+coords+note +scripted-water(a) t0.15"
"""
import argparse
import json
from pathlib import Path

from hoshi7.curve import curve, mean

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "runs" / "ladder" / "results.jsonl"


def show(c: dict) -> None:
    print(f"{c['run']}  {c['agents']}")
    fmt = lambda v: "-" if v is None else f"{v:.2f}"
    print(f"{'day':>3} {'taken':>6} {'open h':>6} {'rep.fail':>8} {'farm/h':>7} {'ref/h':>6} {'ratio':>6} {'refused/h':>9} {'harvest':>7} {'ref':>4}")
    for r in c["rows"]:
        print(f"{r['day']:>3} {fmt(r.get('taken_rate')):>6} {r.get('open', 0):6.0f} {fmt(r.get('repeat_after_fail')):>8} {r['rate']:7.2f} "
              f"{r['ref_rate']:6.2f} {fmt(r['ratio']):>6} {r['refused_per_h']:9.2f} {r['harvest']:7} {r['ref_harvest']:4}")


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

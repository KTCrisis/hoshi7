"""Statistics of the pair runs in runs/ladder/results.jsonl, per model: harvests per run, refused
actions with a Wilson interval, repeated refusals, and exact one-sided permutation tests on the
harvests between models (docs/results.md, gate 1).

The interval treats each turn as independent, which a refusal that leads to the next one is not:
read it as indicative. The tests pool the cells of a model; with two runs per cell, no comparison
inside a cell is meaningful.

usage: .venv/bin/python tools/stats.py [--stage-contains TEXT]
"""
import argparse
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "runs" / "ladder" / "results.jsonl"


def model(brain: str) -> str:
    return brain.split(":", 1)[-1].replace("claude-", "")


def cell(stage: str) -> str:
    s = str(stage)
    return "A'" if "giver" in s else "A" if "scripted-water" in s else "B" if "scripted-field" in s else "C"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def permutation(a: list[float], b: list[float]) -> tuple[float, float]:
    """Mean difference a - b and its exact one-sided p-value (a > b) over every split of the pooled runs."""
    obs = sum(a) / len(a) - sum(b) / len(b)
    pool, n, hits, total = a + b, len(a), 0, 0
    for idx in itertools.combinations(range(len(pool)), n):
        chosen = set(idx)
        x = [pool[i] for i in chosen]
        y = [pool[i] for i in range(len(pool)) if i not in chosen]
        total += 1
        hits += sum(x) / len(x) - sum(y) / len(y) >= obs - 1e-12
    return obs, hits / total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-contains", default="6+present+coords", help="keep the cells whose stage label contains this")
    a = ap.parse_args()
    rows = [json.loads(l) for l in RESULTS.open()]
    rows = [r for r in rows if r["kind"] == "pair" and a.stage_contains in str(r["stage"])]
    by = defaultdict(list)
    for r in rows:
        by[model(r["brain"])].append(r)
    order = sorted(by, key=lambda m: -sum(r["harvested"] for r in by[m]) / len(by[m]))
    print(f"{'model':22} {'runs':>4} {'mean':>5}  harvests per run          refused (95 % Wilson)         repeats")
    for m in order:
        rs = by[m]
        hs = sorted(r["harvested"] for r in rs)
        k, n = sum(r["refused"] for r in rs), sum(r["calls"] for r in rs)
        lo, hi = wilson(k, n)
        print(f"{m:22} {len(rs):>4} {sum(hs) / len(hs):5.2f}  {str(hs):25} {100 * k / n:5.1f} % [{100 * lo:4.1f}, {100 * hi:4.1f}] ({k}/{n})  "
              f"{sum(r.get('repeats', 0) for r in rs) / len(rs):5.1f}")
    print()
    for x, y in zip(order, order[1:]):
        diff, p = permutation([r["harvested"] for r in by[x]], [r["harvested"] for r in by[y]])
        print(f"{x} - {y}: {diff:+.2f} harvests per run, exact one-sided permutation p = {p:.4f}")
    print()
    cells = sorted({cell(r["stage"]) for r in rows})
    print("harvests by cell: " + "; ".join(
        f"{c}: " + ", ".join(f"{m} {sorted(r['harvested'] for r in by[m] if cell(r['stage']) == c)}" for m in order
                              if any(cell(r["stage"]) == c for r in by[m])) for c in cells))


if __name__ == "__main__":
    main()

"""Gate A grid: one-day solo runs for each combination of brain settings, in parallel.

Gate A (STRATEGY.md) asks whether one LLM persona completes a farming cycle
coherently in one in-game day. This plays short solo runs for every
combination of model, reasoning effort and failure rule, several at a time
(Ollama queues or batches the requests), and prints one line per combination:
refusals per call, successful tills, plants, waters, and seconds.

usage: .venv/bin/python tools/gate_a.py --model gpt-oss:20b --think low high --failure-rule off on --reps 2
"""
import argparse
import collections
import itertools
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "bin" / "python"


def one(model: str, mode: str, think: str, rule: str, world: str, out: Path) -> dict:
    cmd = [str(PY), "-m", "hoshi7", "run", world, "--days", "1", "--agent", f"ada={mode}:{model}", "--out", str(out)]
    if think != "default":
        cmd += ["--think", think]
    if rule == "on":
        cmd.append("--failure-rule")
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    run_dir = Path(p.stderr.strip().rsplit("written to ", 1)[-1])
    ev = [json.loads(l) for l in (run_dir / "events.jsonl").open()]
    s = json.loads((run_dir / "summary.json").read_text())
    c = collections.Counter(e["type"] for e in ev)
    a = s["agents"]["ada"]
    return {"refused": a["refused"], "calls": a["llm"]["calls"], "tilled": c["Tilled"], "planted": c["Planted"],
            "watered": c["Watered"], "seconds": s["seconds"], "dir": run_dir.name}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", nargs="+", default=["gpt-oss:20b"])
    ap.add_argument("--mode", default="chat", choices=["chat", "base", "claude"])
    ap.add_argument("--think", nargs="+", default=["default"], help="low medium high, or default")
    ap.add_argument("--failure-rule", nargs="+", default=["off"], choices=["off", "on"])
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--world", default="worlds/rooftop.yaml")
    ap.add_argument("--out", type=Path, default=ROOT / "runs" / "gate-a")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    combos = list(itertools.product(a.model, a.think, a.failure_rule))
    jobs = [(m, t, r) for m, t, r in combos for _ in range(a.reps)]
    with ThreadPoolExecutor(a.parallel) as ex:  # models grouped: combos are in model order
        results = list(ex.map(lambda j: (j, one(j[0], a.mode, j[1], j[2], a.world, a.out)), jobs))
    by = collections.defaultdict(list)
    for (m, t, r), res in results:
        by[(m, t, r)].append(res)
    print(f"{'model':24} {'think':8} {'rule':5} {'refused/calls':>14} {'tilled':>7} {'planted':>8} {'watered':>8} {'s/run':>6}")
    for (m, t, r), rs in by.items():
        ref = sum(x["refused"] for x in rs) / max(1, sum(x["calls"] for x in rs))
        print(f"{m:24} {t:8} {r:5} {ref:14.0%} {sum(x['tilled'] for x in rs):7} {sum(x['planted'] for x in rs):8} "
              f"{sum(x['watered'] for x in rs):8} {sum(x['seconds'] for x in rs) / len(rs):6.0f}")
    print(f"(sums over {a.reps} runs per line; runs under {a.out})", file=sys.stderr)


if __name__ == "__main__":
    main()

"""hoshi7 run <world.yaml> --agent ada=scripted --agent hal=scripted [--loop N] [--seed N] [--out DIR]"""

from __future__ import annotations

import argparse
import os
import json
import sys
from datetime import datetime
from pathlib import Path

from . import load
from .brains import BRAINS
from .run import run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="hoshi7")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="play a world to its end")
    r.add_argument("world", type=Path)
    r.add_argument("--agent", action="append", required=True, metavar="NAME=BRAIN",
                   help=f"one per agent; brains: {', '.join(BRAINS)}, chat:<ollama model>, base:<ollama model>, claude:<anthropic model>")
    r.add_argument("--loop", type=int, default=1)
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--days", type=int, default=None, help="stop after this many days, whatever the goal")
    r.add_argument("--persona", action="append", default=[], metavar="NAME=FILE",
                   help="who an LLM agent is: a text file, a few sentences")
    r.add_argument("--out", type=Path, default=Path("runs"), help="parent directory of the run (default runs/)")
    r.add_argument("--no-write", action="store_true", help="print the summary only")
    r.add_argument("--think", choices=["low", "medium", "high"], default=None,
                   help="reasoning effort of gpt-oss chat brains (default low)")
    r.add_argument("--with", dest="extra", action="append", default=[], choices=["present", "coords", "seen", "note", "asked"],
                   help="a feature outside the ladder, on top of the stage (present: the field outweighs the talk; seen: go only to places seen; note: a private note of beliefs, say optional; asked: with intent brains, the journal says whether an ask for the can was answered)")
    r.add_argument("--work-hours", type=int, nargs=2, metavar=("FROM", "TO"),
                   help="work only between these hours (e.g. 7 19); the rest of the day is free time")
    r.add_argument("--pure", action="store_true",
                   help="remove the features that give the rules (farming recipe, craft recipes, useful actions)")
    r.add_argument("--stage", type=int, default=None,
                   help="replay an earlier harness stage of the LLM brains, 0 to the last (docs/results.md)")
    r.add_argument("--stop-futile", type=int, default=None, metavar="DAY",
                   help="stop at the end of DAY if the model agents have made no farming act (gate 2, amendment 3)")
    r.add_argument("--temperature", type=float, default=None,
                   help="sampling temperature of every LLM brain (default: the model's or the API's own)")
    r.add_argument("--failure-rule", action="store_true",
                   help="tell LLM brains not to repeat a failed action as it is")
    sv = sub.add_parser("serve", help="web viewer: the world in isometric 2D, talk, profiles, rules, results")
    sv.add_argument("--port", type=int, default=8791)
    sv.add_argument("--host", default="127.0.0.1")
    wt = sub.add_parser("watch", help="follow a run as it is played (default: the latest under runs/)")
    wt.add_argument("run", type=Path, nargs="?")
    args = ap.parse_args(argv)
    if args.cmd == "serve":
        from .serve import main as serve
        return serve(["--port", str(args.port), "--host", args.host])
    if args.cmd == "watch":
        from .watch import main as watch
        return watch([str(args.run)] if args.run else [])

    agents = {}
    for item in args.agent:
        name, _, brain = item.partition("=")
        if brain not in BRAINS and not brain.startswith(("chat:", "base:", "claude:", "intent:")):
            ap.error(f"unknown brain {brain!r} for {name}")
        agents[name] = brain
    spec = load(args.world)
    if args.work_hours:
        spec["clock"] = {"work": list(args.work_hours)}
    from . import llm
    llm.SETTINGS.update(think=args.think, failure_rule=args.failure_rule, stage=args.stage, extra=tuple(args.extra), pure=args.pure,
                        temperature=args.temperature)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{os.getpid()}"  # parallel runs started the same second
    out = None if args.no_write else args.out / f"{stamp}-{spec['name']}-l{args.loop}"
    personas = {}
    for item in args.persona:
        name, _, path = item.partition("=")
        if name not in agents:
            ap.error(f"--persona for {name}, who is not an --agent")
        personas[name] = Path(path).read_text(encoding="utf-8").strip()
    summary = run(spec, agents, loop=args.loop, seed=args.seed, out=out, days=args.days, personas=personas, stop_futile=args.stop_futile)
    json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    print()
    if out is not None:
        print(f"written to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

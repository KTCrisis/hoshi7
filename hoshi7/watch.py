"""Follow a run as it is played: the whole map seen from above, the clock,
the harvest, and each agent's last actions and words, refusals included.
Reads the files the runner writes as it goes; it changes nothing.

python -m hoshi7 watch [RUN_DIR]   (default: the latest under runs/)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from .events import from_dict
from .world import World

COLORS = ["\033[38;5;214m", "\033[38;5;45m", "\033[38;5;205m", "\033[38;5;118m"]
DIM, BOLD, RED, OFF = "\033[2m", "\033[1m", "\033[31m", "\033[0m"
SHOWN = 4


def latest(root: Path) -> Path:
    runs = sorted((d for d in root.iterdir() if d.is_dir()), key=lambda d: d.stat().st_mtime)
    if not runs:
        raise SystemExit(f"no run under {root}")
    return runs[-1]


def lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            break  # a line being written
    return out


def cell(w: World, x: int, y: int, color: dict[str, str]) -> str:
    s = w.state
    who = s.occupant(x, y)
    if who is not None:
        return f"{BOLD}{color[who]}{who[0].upper()}{OFF}"
    t = s.tile(x, y)
    if t.crop is not None:
        ripe = t.grown >= s.crops[t.crop]["days"]
        return f"\033[38;5;226m!{OFF}" if ripe else f"\033[38;5;{'40' if t.watered else '64'}m{min(t.grown, 9)}{OFF}"
    if t.tilled:
        return f"\033[38;5;33m*{OFF}" if t.watered else f"\033[38;5;137m={OFF}"
    return f"{DIM}{t.kind}{OFF}"


def frame(run: Path) -> str:
    events = [from_dict(e) for e in lines(run / "events.jsonl")]
    if not events:
        return f"waiting for {run} ..."
    w = World.replay(events)
    s = w.state
    turns = lines(run / "turns.jsonl")
    agents = list(s.agents)
    color = {a: COLORS[i % len(COLORS)] for i, a in enumerate(agents)}
    o = s.objective
    out = [f"{BOLD}{s.world}{OFF} ({s.plane})  day {s.day} {s.hour % 24:02d}:00  "
           f"harvest {s.harvested.get(o['harvest'], 0)}/{o['count']} by day {o['by_day']}"
           + (f"  {BOLD}{s.outcome.upper()}{OFF}" if s.outcome else "")]
    out.append("   " + "".join(str(x % 10) for x in range(s.width)))
    out += [f"{y:2d} " + "".join(cell(w, x, y, color) for x in range(s.width)) for y in range(s.height)]
    out.append(f"{DIM}* watered  = tilled dry  0-9 growing  ! ripe{OFF}")
    for a in agents:
        ag = s.agents[a]
        mine = [t for t in turns if t["agent"] == a][-SHOWN:]
        brain = mine[-1]["brain"] if mine else "?"
        can = f"  can {s.can_charge}" if s.can_holder == a else ""
        inv = ", ".join(f"{k} {v}" for k, v in sorted(ag.inventory.items()))
        out.append(f"\n{BOLD}{color[a]}{a}{OFF} {DIM}{brain}{OFF}  ({ag.x},{ag.y})  energy {ag.energy}{can}  {inv}")
        for t in mine:
            act = next((x for x in t["actions"] if x["type"] != "say"), {"type": "?"})
            said = next((x["text"] for x in t["actions"] if x["type"] == "say"), "")
            refused = next((e.reason for e in events if getattr(e, "agent", None) == a and type(e).__name__ == "Rejected" and e.tick == t["tick"]), None)
            params = " ".join(f"{k}={v}" for k, v in act.items() if k != "type")
            line = f"  {t['tick']:4d} {act['type']} {params}"
            if refused:
                line += f"  {RED}refused: {refused}{OFF}"
            if said:
                line += f'\n         {color[a]}"{said[:110]}"{OFF}'
            out.append(line)
    return "\n".join(out)


def main(argv: list[str]) -> int:
    run = Path(argv[0]) if argv else latest(Path("runs"))
    try:
        while True:
            sys.stdout.write("\033[H\033[2J" + frame(run) + "\n")
            sys.stdout.flush()
            if (run / "summary.json").exists():
                print(f"\n{DIM}run over: {run}/summary.json{OFF}")
                return 0
            time.sleep(1)
    except KeyboardInterrupt:
        return 0

"""A web viewer for runs: the world in 2D isometric, the personas at work, their
talk, each one's profile, the rules met so far, and the results table. Reads the
files the runner writes as it goes (as `hoshi7 watch` does); it changes nothing.

python -m hoshi7 serve [--port 8791] [--host 127.0.0.1]   then open http://localhost:8791
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import time
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .events import from_dict
from .prices import usd
from .watch import lines
from .world import World

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
ARCHIVE = "pre-fix"
WEB = Path(__file__).resolve().parent / "web"
TALK = 300   # lines of the Conversation tab: thought, done, said

# Rules an agent meets through the world's refusals: the reason it reads, the rule
# it states, and the success that shows the rule applied afterwards. Inferred from
# the log, not from what the agent says: "met" = refused at least once,
# "applied" = at least 3 such successes after its last refusal for that reason.
RULES = [
    ("not soil", "only soil can be tilled", "Tilled"),
    ("not tilled", "plant and water only on tilled soil", "Planted"),
    ("already tilled", "a tile is tilled once", "Tilled"),
    ("something grows there already", "one crop per tile", "Planted"),
    ("already watered", "a tile is watered once a day", "Watered"),
    ("not holding the can", "only the can's holder waters", "Watered"),
    ("the can is empty", "the can empties; refill it", "Refilled"),
    ("no source within reach", "refill next to the source", "Refilled"),
    ("the source gives nothing now", "the source gives only at some hours", "Refilled"),
    ("not ripe", "harvest only when ripe", "Harvested"),
    ("nothing grows there", "harvest only where something grows", "Harvested"),
    ("too tired", "energy runs out; it comes back each morning", "DayStarted"),
    ("unknown crop", "plant a crop by its name, not its seed's", "Planted"),
]


WORLDS = {"rooftop": "toit", "rooftop-counter": "toit à l'envers", "conservatory": "serre", "station": "dôme"}
BRAINS = {"haiku": "Haiku", "sonnet": "Sonnet", "gpt-oss": "gpt-oss", "mistral": "Mistral", "scripted": "bot"}


def brain_name(kind: str) -> str:
    k = kind.lower()
    base = " base" if k.startswith("base:") or "-base" in k else ""
    return next((v for key, v in BRAINS.items() if key in k), kind.split(":")[-1]) + base


def label(run: Path, meta: dict[str, Any], summary: dict[str, Any], live: bool) -> str:
    """A name a visitor can read: when, who, where, how long, and what came of it."""
    stamp = run.name[:13]
    when = f"{stamp[6:8]}/{stamp[4:6]} {stamp[9:11]}:{stamp[11:13]}" if stamp[:8].isdigit() else run.name
    personas = meta.get("personas") or summary.get("personas") or {}
    brains = meta.get("agents") or {a: v.get("brain", "") for a, v in summary.get("agents", {}).items()}
    names = [display(personas.get(a, ""), a) if personas.get(a) else brain_name(b) for a, b in brains.items()]
    who = (f"{names[0]} seul" if len(names) == 1 else " et ".join(names)) if names else "?"
    world = meta.get("world") or summary.get("world") or ""
    bits = [when, who, WORLDS.get(world, world)]
    days = (summary.get("day", 1) - 1) if summary else meta.get("days")
    if days:
        bits.append(f"{days} j")
    if meta.get("pure"):
        bits.append("sans règles")
    if live:
        bits.append("en cours")
    elif summary:
        n = sum(summary.get("harvested", {}).values())
        bits.append(f"{n} récolte{'s' if n > 1 else ''}" if n else "aucune récolte")
    return " · ".join(bits)


def runs() -> list[dict[str, Any]]:
    """Every run directory under runs/ and runs/<group>/, newest first; runs/pre-fix/ (played before
    57fa9b5, agents blind to their own refusals) stays out of the list."""
    out = []
    for d in list(RUNS.glob("*/events.jsonl")) + list(RUNS.glob("*/*/events.jsonl")):
        run = d.parent
        if run.relative_to(RUNS).parts[0] == ARCHIVE:
            continue
        meta = json.loads((run / "meta.json").read_text()) if (run / "meta.json").exists() else {}
        summary = json.loads((run / "summary.json").read_text()) if (run / "summary.json").exists() else {}
        mtime = d.stat().st_mtime
        live = not summary and time.time() - mtime < 120
        out.append({"dir": str(run.relative_to(RUNS)), "mtime": mtime, "done": bool(summary), "live": live,
                    "agents": meta.get("agents", {}), "label": label(run, meta, summary, live),
                    "world": meta.get("world", run.name.split("-", 3)[-1])})
    return sorted(out, key=lambda r: -r["mtime"])


def rules_met(events: list[dict[str, Any]], agents: list[str], spec: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for a in agents:
        rows = []
        for reason, rule, success in RULES:
            refusals = [i for i, e in enumerate(events) if e["type"] == "Rejected" and e["agent"] == a
                        and str(e.get("reason", "")).startswith(reason)]
            if not refusals:
                continue
            after = sum(1 for e in events[refusals[-1] + 1:] if e["type"] == success and e.get("agent", a) == a)
            rows.append({"rule": rule, "refused": len(refusals), "after": after,
                         "status": "applied" if after >= 3 else "met"})
        rows += growth(events, a, spec)
        out[a] = rows
    return out


def growth(events: list[dict[str, Any]], a: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """The growth rule is never refused: read it from the waterings of planted tiles, day by day."""
    dry = any(c.get("grows_when") == "dry" for c in spec.get("crops", {}).values())
    per_day: list[int] = [0]  # day 1 has no DayStarted
    planted: set[tuple[int, int]] = set()
    for e in events:
        if e["type"] == "DayStarted":
            per_day.append(0)
        elif e["type"] == "Planted":
            planted.add((e["x"], e["y"]))
        elif e["type"] == "Harvested":
            planted.discard((e["x"], e["y"]))
        elif e["type"] == "Watered" and e["agent"] == a and (e["x"], e["y"]) in planted:
            per_day[-1] += 1
    if not any(per_day) and not dry:
        return []
    rule = "crops grow on dry days" if dry else "crops grow on watered days"
    if dry:
        status = "applied" if len(per_day) >= 2 and per_day[-1] == 0 and max(per_day[:-1]) > 0 else (
            "met" if len(per_day) >= 2 and per_day[-1] < max(per_day[:-1]) else "not yet")
    else:
        status = "applied" if sum(1 for n in per_day if n > 0) >= 2 else "met"
    return [{"rule": rule, "refused": 0, "after": per_day, "status": status, "growth": True}]


def display(persona: str, agent: str) -> str:
    """The name to show: the persona's own ("You are LEDGER-7, ..." -> LEDGER-7), else the agent id."""
    if not persona.startswith("You are "):
        return agent
    return persona[8:].split(",")[0].split(".")[0].strip() or agent


def sprite(persona: str) -> str:
    """The sprite file for a persona, from the name after "You are": "You are LEDGER-7, ..." -> ledger7."""
    if not persona.startswith("You are "):
        return ""
    name = persona[8:].split(",")[0].split(".")[0]
    return "".join(ch for ch in name.lower() if ch.isalnum())


def timeline(raw: list[dict[str, Any]]) -> list[list[int]]:
    """[log index, day, hour] at the start of the run and after every hour that passed: the
    points a replay can stop at. The state at a point is the log replayed up to its index."""
    start = next((i for i, e in enumerate(raw) if e["type"] not in ("Created", "Joined")), len(raw))
    out = [[start, 1, 6]]
    for i, e in enumerate(raw):
        if e["type"] == "HourPassed":
            out.append([i + 1, e.get("day", out[-1][1]), e.get("hour", 6) % 24])
        elif e["type"] == "DayStarted":
            out.append([i + 1, e.get("day", out[-1][1] + 1), 6])
    if out[-1][0] < len(raw):
        out.append([len(raw), out[-1][1], out[-1][2]])
    return out


ACTED = {"Tilled": "till", "Planted": "plant", "Watered": "water", "Harvested": "harvest", "Gathered": "gather",
         "Examined": "examine", "Crafted": "craft", "Gave": "give", "Refilled": "refill", "Waited": "wait",
         "Moved": "move", "Rejected": "refused"}


def snapshot(rel: str, at: int | None = None) -> dict[str, Any]:
    """The run as it stands, or as it stood at log index `at` (replay)."""
    run = (RUNS / rel).resolve()
    if RUNS.resolve() not in run.parents:
        raise ValueError("outside runs/")
    full = lines(run / "events.jsonl")
    if not full:
        return {"waiting": True}
    raw = full if at is None else full[:max(1, min(at, len(full)))]
    w = World.replay([from_dict(e) for e in raw])
    s = w.state
    turns = [t for t in lines(run / "turns.jsonl") if t.get("at", 0) < len(raw)]
    meta = json.loads((run / "meta.json").read_text()) if (run / "meta.json").exists() else {}
    summary = json.loads((run / "summary.json").read_text()) if (run / "summary.json").exists() else {}
    spec = raw[0]
    grid = [[{"k": t.kind, "t": t.tilled, "w": t.watered, "c": t.crop, "g": t.grown,
              "r": t.crop is not None and t.grown >= s.crops[t.crop]["days"]} for t in row] for row in s.grid]
    clock: dict[int, tuple[int, int]] = {}
    day, hour = 1, 6
    talk = []
    when: dict[int, tuple[int, int]] = {}      # tick -> (day, hour), for the notes, which live in the turns
    for e in raw:
        if e["type"] == "DayStarted":
            day, hour = e.get("day", day), 6
        elif e["type"] == "HourPassed":
            day, hour = e.get("day", day), e.get("hour", hour)
        elif e["type"] == "Said":
            talk.append({"kind": "said", "tick": e["tick"], "agent": e["agent"], "day": day, "hour": hour % 24, "text": e["text"]})
        elif e["type"] in ACTED and not (e["type"] == "Rejected" and e.get("action") == "say"):
            # What was done, as the world recorded it, by every agent (bots included): a refusal too.
            act = {k: e[k] for k in ("x", "y", "crop", "item", "to", "recipe", "yields", "action", "reason", "qty") if k in e}
            talk.append({"kind": "act", "tick": e["tick"], "agent": e["agent"], "day": day, "hour": hour % 24,
                         "act": ACTED[e["type"]], **act})
        when.setdefault(e["tick"], (day, hour % 24))
    # What was thought: the private notes (`--with note`), heard by no one; before what was said that hour.
    for t in lines(run / "turns.jsonl"):
        note = (t.get("llm") or {}).get("note")
        if note and t.get("at", 0) < len(raw):
            d, h = when.get(t["tick"], (day, hour % 24))
            talk.append({"kind": "note", "tick": t["tick"], "agent": t["agent"], "day": d, "hour": h,
                         "partner": note.get("partner", ""), "world": note.get("world", "")})
    talk.sort(key=lambda l: (l["tick"], {"note": 0, "act": 1, "said": 2}[l["kind"]]))   # thought, deed, word
    refused = Counter(e["agent"] for e in raw if e["type"] == "Rejected")
    reasons: dict[str, Counter] = defaultdict(Counter)
    for e in raw:
        if e["type"] == "Rejected":
            reasons[e["agent"]][str(e.get("reason", ""))[:40]] += 1
    # What each agent last did, as the world recorded it (a refusal included, a word said not): the
    # viewer shows it above the figure for the hour it happened.
    acted: dict[str, dict[str, Any]] = {}
    for e in raw:
        kind = ACTED.get(e["type"])
        if kind and not (kind == "refused" and e.get("action") == "say"):
            acted[e["agent"]] = {"kind": kind, "tick": e["tick"]}
    agents = {}
    personas = meta.get("personas") or summary.get("personas") or {}
    for a in s.agents.values():
        mine = [t for t in turns if t["agent"] == a.id]
        llm = (mine[-1].get("llm") if mine else None) or {}
        agents[a.id] = {
            "x": a.x, "y": a.y, "energy": a.energy, "inventory": a.inventory, "can": s.can_holder == a.id,
            "brain": (mine[-1]["brain"] if mine else meta.get("agents", {}).get(a.id, "")),
            "persona": personas.get(a.id, ""), "sprite": sprite(personas.get(a.id, "")),
            "name": display(personas.get(a.id, ""), a.id), "stage": llm.get("stage"), "extra": llm.get("extra", []),
            "act": acted.get(a.id),
            "turns": len(mine), "refused": refused[a.id], "reasons": reasons[a.id].most_common(6),
            "last": [{"actions": t["actions"], "tick": t["tick"]} for t in mine[-6:]],
            "note": next((t["llm"]["note"] for t in reversed(mine) if t.get("llm", {}).get("note")), None),
            "tokens": [sum(t.get("llm", {}).get("tin", 0) for t in mine), sum(t.get("llm", {}).get("tout", 0) for t in mine)],
        }
    return {"world": s.world, "plane": s.plane, "day": s.day, "hour": s.hour % 24, "tick": s.tick,
            "objective": s.objective, "harvested": s.harvested, "outcome": s.outcome, "can": s.can,
            "can_holder": s.can_holder, "can_charge": s.can_charge, "max_energy": s.max_energy, "clock": s.clock,
            "tiles": s.tiles, "crops": s.crops, "grid": grid,
            "agents": agents, "talk": talk[-TALK:], "rules": rules_met(raw, list(s.agents), spec),
            "done": bool(summary), "meta": meta, "at": len(raw), "timeline": timeline(full),
            "stale": not summary and time.time() - (run / "events.jsonl").stat().st_mtime > 120}


#: The learning curves of the hybrid cells, computed once per state of results.jsonl (a replay of each run).
_CURVES: dict[str, Any] = {"mtime": None, "cells": {}}


def learning(cell: tuple, rs: list[dict[str, Any]], mtime: float) -> dict[str, list]:
    """Per day, the mean share of opportunities taken and of repeats after a failed intention (hoshi7/curve.py),
    for a hybrid cell; empty for the others, whose turns carry no intention."""
    if _CURVES["mtime"] != mtime:
        _CURVES.update(mtime=mtime, cells={})
    if cell not in _CURVES["cells"]:
        out: dict[str, list] = {}
        if cell[1].startswith("intent:") and cell[0] == "pair":
            from .curve import curve, mean
            dirs = [RUNS / "ladder" / r["run"] for r in rs if (RUNS / "ladder" / r["run"] / "events.jsonl").exists()]
            if dirs:
                m = mean([curve(d) for d in dirs])
                out = {"taken": [r.get("taken_rate") for r in m], "repeat_fail": [r.get("repeat_after_fail") for r in m]}
        _CURVES["cells"][cell] = out
    return _CURVES["cells"][cell]


def results() -> list[dict[str, Any]]:
    path = RUNS / "ladder" / "results.jsonl"
    rows = [json.loads(l) for l in path.open()] if path.exists() else []
    mtime = path.stat().st_mtime if path.exists() else 0.0
    by: dict[tuple, list] = defaultdict(list)
    for r in rows:
        tag = "" if r.get("personas", []) in ([], ["vesper", "ledger7"]) else " " + "/".join(r["personas"])
        by[(r["kind"], r["brain"], f"{r['stage']}{tag}", r.get("days", 0))].append(r)   # cells as in tools/ladder.py
    out = []
    for (kind, brain, stage, days), rs in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1], len(kv[0][2]) > 1, kv[0][2], kv[0][3])):
        n = len(rs)
        costs = [usd(brain, r["tin"], r["tout"], r.get("tcw", 0), r.get("tcr", 0)) for r in rs]
        cost = None if None in costs else sum(costs) / n
        out.append({"kind": kind, "brain": brain, "stage": f"{stage} · {days} j", "n": n,
                    "refused": sum(r["refused"] for r in rs) / max(1, sum(r["calls"] for r in rs)),
                    "planted": sum(r["planted"] for r in rs) / n, "harvested": sum(r["harvested"] for r in rs) / n,
                    "can": sum(r["can_moves"] for r in rs) / n, "usd": cost,
                    **{k: sum(r.get(k, 0) for r in rs) / n for k in ("repeats", "alloy", "copper", "decoys", "examined", "seeds_made")},
                    "learning": learning((kind, brain, stage, days), rs, mtime)})
    return out


# A shared password, as on sup.flux7.art: set HOSHI7_PASSWORD in the environment (never in the
# repository) and every page asks for it once; the cookie is an HMAC of the password, so changing
# the password logs everyone out. Unset, the viewer is open (local use).
PASSWORD = os.environ.get("HOSHI7_PASSWORD", "")
COOKIE = "hoshi7"
LOGIN = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>hoshi7</title><style>body{margin:0;height:100vh;display:grid;place-items:center;background:#0b0e14;color:#c9d4e3;
font:14px ui-monospace,monospace}form{display:flex;gap:8px}input,button{font:inherit;padding:6px 10px;background:#111722;
color:#c9d4e3;border:1px solid #1f2a3a}h1{color:#4de1ff;font-size:15px;letter-spacing:.08em;text-align:center}p{color:#ff6b6b}</style>
</head><body><div><h1>HOSHI7</h1><form method="post" action="/login"><input type="password" name="password"
placeholder="mot de passe" autofocus><button>entrer</button></form>{error}</div></body></html>"""


def token() -> str:
    return hmac.new(hashlib.sha256(PASSWORD.encode()).digest(), b"hoshi7 viewer", hashlib.sha256).hexdigest()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass

    def send(self, code: int, body: bytes, ctype: str, headers: dict[str, str] | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def allowed(self) -> bool:
        if not PASSWORD:
            return True
        cookies = dict(c.strip().split("=", 1) for c in self.headers.get("Cookie", "").split(";") if "=" in c)
        return hmac.compare_digest(cookies.get(COOKIE, ""), token())

    def login(self, error: str = "") -> None:
        self.send(401, LOGIN.replace("{error}", f"<p>{error}</p>" if error else "").encode(), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/login" or not PASSWORD:
            return self.send(404, b"", "text/plain")
        n = min(int(self.headers.get("Content-Length", 0) or 0), 4096)
        given = parse_qs(self.rfile.read(n).decode(errors="replace")).get("password", [""])[0]
        if not hmac.compare_digest(given.encode(), PASSWORD.encode()):
            time.sleep(2)  # a guess every two seconds at most, per connection
            return self.login("mot de passe incorrect")
        self.send(303, b"", "text/plain", {"Location": "/", "Set-Cookie":
                  f"{COOKIE}={token()}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age={30 * 24 * 3600}"})

    def do_GET(self) -> None:
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if not self.allowed():
            return self.login() if not u.path.startswith("/api/") else self.send(401, b"{}", "application/json")
        try:
            if u.path == "/":
                return self.send(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
            if u.path.startswith(("/sprites/", "/tiles/")):
                f = (WEB / u.path.split("/")[1] / Path(u.path).name)
                if f.exists():
                    return self.send(200, f.read_bytes(), "image/png")
                return self.send(404, b"", "text/plain")
            if u.path == "/api/runs":
                data: Any = runs()
            elif u.path == "/api/run":
                data = snapshot(q["dir"][0], int(q["at"][0]) if "at" in q else None)
            elif u.path == "/api/results":
                data = results()
            else:
                return self.send(404, b"not found", "text/plain")
            self.send(200, json.dumps(data, ensure_ascii=False).encode(), "application/json")
        except (KeyError, ValueError, OSError) as err:
            self.send(400, json.dumps({"error": str(err)}).encode(), "application/json")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="hoshi7 serve")
    ap.add_argument("--port", type=int, default=8791)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args(argv)
    print(f"hoshi7 viewer on http://{a.host}:{a.port}")
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()

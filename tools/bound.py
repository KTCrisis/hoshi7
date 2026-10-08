"""An upper bound on the harvest of a pair, for a number of days: what an all-seeing planner commanding
both agents could reach at most. Scripted bots, models and hybrids are read against it (the gap to the
optimum), and it says how much any tuning can still win.

It is a relaxation, solved as an integer linear program (scipy's HiGHS), at the scale of the day:

- crops are planted in daily cohorts; a cohort is watered on four consecutive days from its planting
  day and harvested the day after its fourth watering (no reason to wait longer);
- each agent has the world's hours a day (DAY_START to DAY_END) and its energy (till 2, water 1);
- one can: at most one watering an hour for the pair, the holder's hours bound the watering;
- every ten waterings (the can's size) a refill trip: walk to the source, refill, walk back, counted
  with the shortest walk from the trays (MOVE_RANGE steps an hour);
- an agent acts on its own tile and the four next to it, so k tiles cost at least ceil(k / 5) moves;
  walking between the trays and anything else is otherwise free (optimistic);
- trays: at most the world's soil tiles in use at once; a tray once tilled stays tilled;
- seeds: the pair's starting seeds, then the recipe (one harvest makes two seeds, one hour of craft).

Everything left out (walking between distant tiles, who stands where, the can changing hands) can only
lower the true optimum, so the number is a ceiling, not a target that must be reachable.

usage: .venv/bin/python tools/bound.py [--world worlds/rooftop.yaml] [--days 6 12 18 28]
"""
from __future__ import annotations

import argparse
import math
from collections import deque
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from hoshi7 import load
from hoshi7.world import COST, DAY_END, DAY_START, MOVE_RANGE

ROOT = Path(__file__).resolve().parent.parent
HOURS = DAY_END - DAY_START
AGENTS = 2
REACH = 5   # one's own tile and the four next to it


def refill_trip(spec: dict) -> int:
    """Hours of one refill trip from the nearest tray: walk to a tile next to the source, refill, walk back."""
    rows = [r for r in spec["map"].splitlines() if r]
    tiles = spec["tiles"]
    walk = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if tiles[c].get("walk")}
    soil = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if tiles[c].get("soil")}
    source = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if tiles[c].get("source")}
    goal = {p for p in walk if any((p[0] + dx, p[1] + dy) in source for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)))}
    dist = {p: 0 for p in soil}
    q = deque(soil)
    while q:
        p = q.popleft()
        if p in goal:
            steps = dist[p]
            moves = math.ceil(steps / MOVE_RANGE) if steps else 0
            return 2 * moves + 1
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            n = (p[0] + dx, p[1] + dy)
            if n in walk and n not in dist:
                dist[n] = dist[p] + 1
                q.append(n)
    raise ValueError("no source reachable from the trays")


def bound(spec: dict, days: int) -> dict:
    crop = next(iter(spec["crops"].values()))
    grow = int(crop["days"])
    seeds_name = crop["seeds"]
    recipe = next((r for r in spec.get("recipes", {}).values() if seeds_name in r["makes"]), None)
    per_craft = recipe["makes"][seeds_name] if recipe else 0
    seeds0 = sum(s.get("inventory", {}).get(seeds_name, 0) for s in spec["spawns"][:AGENTS])
    trays = sum(1 for r in spec["map"].splitlines() for c in r if spec["tiles"][c].get("soil"))
    can = int(spec.get("can", {}).get("size", 0))
    energy = int(spec["max_energy"])
    trip = refill_trip(spec)

    D = days
    # Variables per day d (1..D): n planted, w watered, r refills, t tilled, c crafted, mw watering moves,
    # mf field moves. h (harvest on day d) is n[d - grow - 1]... written as n of an earlier day.
    names = ["n", "w", "r", "t", "c", "mw", "mf"]
    idx = {(v, d): i for i, (v, d) in enumerate((v, d) for v in names for d in range(1, D + 1))}
    N = len(idx)
    harvest_day = lambda d: d + grow   # watered on d .. d + grow - 1, harvested the next day

    def row():
        return np.zeros(N)

    A, lo, hi = [], [], []

    def add(a, l, h):
        A.append(a); lo.append(l); hi.append(h)

    def harvested_on(k):
        """The coefficients of the harvest on day k: the cohort planted grow days before."""
        a = row()
        d = k - grow
        if 1 <= d <= D:
            a[idx["n", d]] = 1
        return a

    for k in range(1, D + 1):
        # Waterings on day k: every cohort still growing.
        a = row(); a[idx["w", k]] = 1
        for d in range(max(1, k - grow + 1), k + 1):
            a[idx["n", d]] -= 1
        add(a, 0, 0)
        # Trays in use on day k at most the soil tiles; a cohort harvested on day k frees its tray that day.
        a = row()
        for d in range(max(1, k - grow + 1), k + 1):
            a[idx["n", d]] = 1
        add(a, 0, trays)
        # Tilled trays (cumulative) cover the trays in use.
        a = row()
        for j in range(1, k + 1):
            a[idx["t", j]] = 1
        for d in range(max(1, k - grow + 1), k + 1):
            a[idx["n", d]] -= 1
        add(a, 0, np.inf)
        # Refills: one trip every `can` waterings (the can starts full).
        a = row(); a[idx["r", k]] = can
        a[idx["w", k]] = -1
        add(a, -can if k == 1 else 0, np.inf)
        # Moves: k tiles worked cost at least ceil(k / 5) positions.
        a = row(); a[idx["mw", k]] = REACH; a[idx["w", k]] = -1
        add(a, 0, np.inf)
        a = row(); a[idx["mf", k]] = REACH; a[idx["t", k]] = -1; a[idx["n", k]] = -1
        a += -harvested_on(k)
        add(a, 0, np.inf)
        # Hours: the can's work fits in one agent's day (one can), the whole in the pair's.
        a = row(); a[idx["w", k]] = 1; a[idx["r", k]] = trip; a[idx["mw", k]] = 1
        add(a, 0, HOURS)
        a = row()
        for v in ("w", "t", "n", "c", "mw", "mf"):
            a[idx[v, k]] = 1
        a[idx["r", k]] = trip
        a += harvested_on(k)
        add(a, 0, AGENTS * HOURS)
        # Energy: the holder's waterings within one agent's energy, tilling and watering within the pair's.
        a = row(); a[idx["w", k]] = COST["water"]
        add(a, 0, energy)
        a = row(); a[idx["w", k]] = COST["water"]; a[idx["t", k]] = COST["till"]
        add(a, 0, AGENTS * energy)
        # Seeds: planted up to day k within the start, plus what crafts made before.
        a = row()
        for j in range(1, k + 1):
            a[idx["n", j]] = 1
            a[idx["c", j]] -= per_craft
        add(a, -np.inf, seeds0)
        # Crafts consume harvests: crafted up to day k within harvested up to day k.
        a = row()
        for j in range(1, k + 1):
            a[idx["c", j]] = 1
            a -= harvested_on(j)
        add(a, -np.inf, 0)
        # A cohort must be harvested within the run: none planted too late to ripen.
        if harvest_day(k) > D:
            a = row(); a[idx["n", k]] = 1
            add(a, 0, 0)

    # Tilling once per tray in all.
    a = row()
    for k in range(1, D + 1):
        a[idx["t", k]] = 1
    add(a, 0, trays)

    obj = -sum(harvested_on(k) for k in range(1, D + 1))
    res = milp(c=obj, constraints=LinearConstraint(np.array(A), lo, hi),
               integrality=np.ones(N), bounds=Bounds(0, np.inf), options={"time_limit": 60})
    if res.x is None:
        raise RuntimeError(f"no solution: {res.message}")
    x = np.round(res.x).astype(int)
    get = lambda v: [int(x[idx[v, d]]) for d in range(1, D + 1)]
    return {"days": D, "harvest": int(round(-res.fun)), "planted": get("n"), "watered": get("w"),
            "tilled": get("t"), "crafted": get("c"), "optimal": res.status == 0, "refill_trip_hours": trip}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="worlds/rooftop.yaml")
    ap.add_argument("--days", type=int, nargs="*", default=[6, 12, 18, 28])
    a = ap.parse_args()
    spec = load(ROOT / a.world)
    for d in a.days:
        b = bound(spec, d)
        print(f"{d:3} days: at most {b['harvest']:3} harvests{'' if b['optimal'] else ' (time limit: not proven optimal)'}"
              f"  · planted per day {b['planted']}  · watered per day {b['watered']}")


if __name__ == "__main__":
    main()

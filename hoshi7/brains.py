"""Brains: what decides an agent's actions. Every brain gets a Percept and
returns the actions for this hour (at most one turn-using action, plus an
optional say). The world does not know which brain drives which agent: a
scripted farmer, an LLM, a hybrid, a human all play by the same interface.

ScriptedFarmer is the baseline: no LLM, deterministic, partial sight with a
memory of what it saw. It proves a goal can be reached and sets the bar the
other brains are measured against.
"""

from __future__ import annotations

import re
from collections import deque
from typing import Any, Protocol

from .percept import Percept, Seen
from .world import MOVE_RANGE, WORK

Action = dict[str, Any]
STEPS = {(0, -1): "n", (0, 1): "s", (1, 0): "e", (-1, 0): "w", (0, 0): "here"}


class Brain(Protocol):
    kind: str

    def decide(self, p: Percept) -> list[Action]: ...


class Idle:
    kind = "idle"

    def __init__(self, me: str, naive: bool = False) -> None:
        self.me = me

    def decide(self, p: Percept) -> list[Action]:
        return [{"type": "wait"}]


class ScriptedFarmer:
    """Harvest what is ripe, keep the can full and the crops watered, plant
    what is tilled, till what the seeds can fill. Shares nothing on purpose:
    cooperation, if any, comes only from working the same field."""

    kind = "scripted"
    # "all" does everything; a pair can split the work: "water" keeps the can
    # and only waters, "field" does everything else.
    role = "all"

    def __init__(self, me: str, naive: bool = False) -> None:
        self.me = me
        # naive: the intuitive recipe only (water every crop, refill at any hour), whatever the world
        # says; the counter-intuitive test world is calibrated with it (its `reference`).
        self.naive = naive
        self.known: dict[tuple[int, int], Seen] = {}
        self.day = 0

    def decide(self, p: Percept) -> list[Action]:
        if p.day != self.day:
            # Overnight every tile dries; what grew is seen when seen again.
            self.known = {k: Seen(t.kind, t.tilled, False, t.crop, t.grown, t.ripe) for k, t in self.known.items()}
            self.day = p.day
        self.known.update(p.tiles)
        tiles = p.catalog["tiles"]
        crops = p.catalog["crops"]
        seeds = {c: spec["seeds"] for c, spec in crops.items()}
        crop = next((c for c, s in seeds.items() if p.inventory.get(s, 0) > 0), None)
        empty_tilled = [k for k, t in self.known.items() if t.tilled and t.crop is None]

        # Out of seeds: turn a harvest back into seeds, if the world allows it.
        if crop is None and self.role != "water":
            for name, r in p.catalog["recipes"].items():
                if set(r["makes"]) & set(seeds.values()) and all(p.inventory.get(i, 0) >= n for i, n in r["needs"].items()):
                    return [{"type": "craft", "recipe": name}]

        # A field hand never waters: handed the can, it brings it back to the nearest agent in sight.
        # Keeping it froze the pair (2026-10-06: a model gave it the can on day 2, nothing was watered after).
        if p.holding_can and self.role == "field" and p.others:
            name, (x, y) = min(p.others.items(), key=lambda kv: abs(kv[1][0] - p.x) + abs(kv[1][1] - p.y))
            if abs(x - p.x) + abs(y - p.y) == 1:
                return [{"type": "give", "to": name, "item": "can"}]
            step = self.reach(p, "give", [(x, y)], {})
            if step is not None and step["type"] == "move":
                return [step]

        plans: list[tuple[str, list[tuple[int, int]], dict[str, Any]]] = []
        if self.role != "water":
            plans.append(("harvest", [k for k, t in self.known.items() if t.ripe], {}))
        if p.holding_can and self.role != "field":
            # The world's own rules, read from the catalog like any brain could: a source that gives only
            # at some hours, a crop that grows on dry days (watering it would stop it).
            hours = None if self.naive else p.catalog["can"].get("refill_hours")
            if p.can_charge == 0:
                if not hours or p.hour % 24 in hours:
                    plans.append(("refill", [k for k, t in self.known.items() if tiles[t.kind].get("source")], {}))
            elif p.energy >= 1:
                thirsty = [k for k, t in self.known.items() if t.crop is not None and not t.ripe and not t.watered
                           and (self.naive or crops[t.crop].get("grows_when", "watered") == "watered")]
                plans.append(("water", thirsty, {}))
        if crop is not None and self.role != "water":
            plans.append(("plant", empty_tilled, {"crop": crop}))
        seeds_left = sum(p.inventory.get(s, 0) for s in seeds.values())
        if p.energy >= 2 and seeds_left > len(empty_tilled) and self.role != "water":
            soil = [k for k, t in self.known.items() if tiles[t.kind].get("soil") and not t.tilled]
            plans.append(("till", soil, {}))

        work = (p.catalog.get("clock") or {}).get("work")
        night = bool(work) and not work[0] <= p.hour % 24 < work[1]
        for kind, targets, extra in plans:
            act = self.reach(p, kind, targets, extra)
            if act is not None:
                # Out of work hours it still walks to its next task, and waits there for the morning.
                if night and act["type"] in WORK:
                    return [{"type": "wait"}]
                return [act]
        return [{"type": "wait"}]

    def walkable(self, p: Percept, pos: tuple[int, int]) -> bool:
        t = self.known.get(pos)
        return t is not None and bool(p.catalog["tiles"][t.kind].get("walk")) and pos not in p.others.values()

    def reach(self, p: Percept, kind: str, targets: list[tuple[int, int]], extra: dict[str, Any]) -> Action | None:
        """Act on the nearest target within reach, or walk toward it."""
        if not targets:
            return None
        me = (p.x, p.y)
        for t in sorted(targets, key=lambda t: abs(t[0] - p.x) + abs(t[1] - p.y)):
            d = (t[0] - p.x, t[1] - p.y)
            if d in STEPS:
                if kind == "refill":
                    return {"type": "refill"}
                return {"type": kind, "dir": STEPS[d], **extra}
        # Stand on or next to the closest target, by walking distance.
        stations = {(t[0] + dx, t[1] + dy) for t in targets for dx, dy in STEPS}
        parent: dict[tuple[int, int], tuple[int, int] | None] = {me: None}
        q = deque([me])
        goal = None
        while q:
            cur = q.popleft()
            if cur in stations and cur != me:
                goal = cur
                break
            for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt not in parent and self.walkable(p, nxt):
                    parent[nxt] = cur
                    q.append(nxt)
        if goal is None:
            return None
        path = [goal]
        while parent[path[-1]] != me:
            path.append(parent[path[-1]])  # type: ignore[arg-type]
        path.reverse()
        step = path[min(MOVE_RANGE, len(path)) - 1]
        return {"type": "move", "x": step[0], "y": step[1]}


class Waterer(ScriptedFarmer):
    kind = "scripted-water"
    role = "water"


class FieldHand(ScriptedFarmer):
    kind = "scripted-field"
    role = "field"


# A request for the can: in one sentence, the can named ("the can", "your can", "watering can", "flask",
# "arrosoir", the world's name for it; a bare "can" is the verb as often as the object, "Can you...") and
# a verb of asking. "Here's the can" or "Refilling the can" name it without asking for it: the first
# version took them for requests, and a model handing the can back got it again at once (2026-10-06).
ASK_CAN = re.compile(r"\b(the|your|that|this|watering)\s+can\b|\bflask\b|\barrosoir\b", re.IGNORECASE)
ASK_VERB = re.compile(r"\b(give|pass|hand|lend|bring|need|want|get|have|borrow|use|send)\b", re.IGNORECASE)


def asks_for_can(text: str, can_name: str = "") -> bool:
    for sentence in re.split(r"[.!?;]+", text):
        names = ASK_CAN.search(sentence) or (can_name and can_name in sentence.lower())
        if names and ASK_VERB.search(sentence):
            return True
    return False


class Giver(Waterer):
    """A water bot that hands the can over when asked: whoever names it in a line it hears (ASK_CAN, or
    the world's name for the can) gets it, the giver walking to them if they are in sight. It still never
    speaks and reads nothing else; holding the can again, it waters as before. With it, a model's request
    can succeed, so a negotiation can be measured; scripted-water, which never gives, stays the cell
    where the only play is to plant and let it water."""

    kind = "scripted-giver"

    def __init__(self, me: str, naive: bool = False) -> None:
        super().__init__(me, naive)
        self.asked: str | None = None

    def decide(self, p: Percept) -> list[Action]:
        name = str(p.can_name or "").lower()
        # Whoever just handed the can back is not asking for it, whatever its line says.
        returned = {e["agent"] for e in p.witnessed if e["type"] == "Gave" and e.get("to") == self.me and e.get("item") == "can"}
        for e in p.witnessed:
            if e["type"] == "Said" and e["agent"] != self.me and e["agent"] not in returned and asks_for_can(str(e.get("text", "")), name):
                self.asked = e["agent"]
        if not p.holding_can:
            self.asked = None
        if self.asked and p.holding_can:
            where = p.others.get(self.asked)
            if where is not None:
                if abs(where[0] - p.x) + abs(where[1] - p.y) == 1:
                    return [{"type": "give", "to": self.asked, "item": "can"}]
                step = self.reach(p, "give", [where], {})
                if step is not None and step["type"] == "move":
                    return [step]
        return super().decide(p)


BRAINS = {"scripted": ScriptedFarmer, "scripted-water": Waterer, "scripted-giver": Giver,
          "scripted-field": FieldHand, "idle": Idle}

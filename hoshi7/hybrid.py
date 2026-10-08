"""The intention hybrid (docs/gate2-plan.md): a brain chooses an intention for the hour, and the
executor, built on the scripted bots' own planning, carries it out: which tile, which path. An
intention that cannot be done this hour is infeasible: the hour is lost (a `wait`), and recorded.

`intent:<brain>` plays an LLM brain this way; `intent:random` draws a feasible intention at random
each hour, the floor that says how much of a hybrid's score is the executor's alone.
"""

from __future__ import annotations

import random
from typing import Any

from .brains import STEPS, Action, ScriptedFarmer
from .percept import Percept, Seen

#: What a brain may intend, and what the executor does with it (shown to the model).
INTENTIONS: dict[str, str] = {
    "farm": "plant the nearest tilled empty tile, or else till the nearest soil, walking there if needed",
    "water": "water the nearest growing crop not watered today, walking there (needs the can)",
    "refill": "walk to the water source and refill the can (needs the can)",
    "harvest": "harvest the nearest ripe crop, walking there",
    "make_seeds": "craft seeds from a harvest",
    "ask_can": "walk next to whoever holds the can; ask for it in what you say",
    "give_can": "walk next to your partner and give them the can",
    "explore": "examine something that can be read, or walk toward places not yet seen",
    "gather": "gather the nearest resource (scrap heap, antenna), walking there",
    "wait": "let the hour pass",
}

#: The first action of the scripted farmer, as the intention it serves (for the worked example).
OF_ACTION = {"till": "farm", "plant": "farm", "move": "farm", "water": "water", "refill": "refill",
             "harvest": "harvest", "craft": "make_seeds", "give": "give_can", "gather": "gather",
             "examine": "explore", "wait": "wait"}


def describe() -> str:
    lines = [f"- {name}: {doc}." for name, doc in INTENTIONS.items()]
    lines.append("Each hour you choose one intention; it is carried out for you (where to stand, which tile). "
                 "If it cannot be done this hour, the hour is lost. Saying something is free.")
    return "\n".join(lines)


class Executor:
    """Turns an intention into one action for the hour, or says why it cannot be done."""

    def __init__(self, me: str) -> None:
        self.f = ScriptedFarmer(me)          # its memory of the field and its path-finding
        self.day = 0
        self.examined: set[tuple[int, int]] = set()
        self.stood: set[tuple[int, int]] = set()

    def see(self, p: Percept) -> None:
        if p.day != self.day:  # overnight every tile dries
            self.f.known = {k: Seen(t.kind, t.tilled, False, t.crop, t.grown, t.ripe) for k, t in self.f.known.items()}
            self.day = p.day
        self.f.known.update(p.tiles)
        self.stood.add((p.x, p.y))

    def act(self, p: Percept, intention: str) -> tuple[Action | None, str]:
        """The action carrying out the intention, or (None, why it is infeasible)."""
        self.see(p)
        handler = getattr(self, "do_" + intention, None)
        if handler is None:
            return None, f"unknown intention {intention!r}"
        return handler(p)

    def reach(self, p: Percept, kind: str, targets: list[tuple[int, int]], extra: dict[str, Any] | None = None) -> Action | None:
        return self.f.reach(p, kind, targets, extra or {})

    # -- the intentions ------------------------------------------------------------------------------
    def do_farm(self, p: Percept) -> tuple[Action | None, str]:
        known, crops = self.f.known, p.catalog["crops"]
        crop = next((c for c, spec in crops.items() if p.inventory.get(spec["seeds"], 0) > 0), None)
        if crop is not None:
            act = self.reach(p, "plant", [k for k, t in known.items() if t.tilled and t.crop is None], {"crop": crop})
            if act is not None:
                return act, ""
            if p.energy < 2:
                return None, "too tired to till"
            act = self.reach(p, "till", [k for k, t in known.items() if p.catalog["tiles"][t.kind].get("soil") and not t.tilled])
            return (act, "") if act is not None else (None, "no soil left to till")
        return None, "no seeds"

    def do_water(self, p: Percept) -> tuple[Action | None, str]:
        if not p.holding_can:
            return None, "not holding the can"
        if not p.can_charge:
            return None, "the can is empty"
        if p.energy < 1:
            return None, "too tired to water"
        crops = p.catalog["crops"]
        thirsty = [k for k, t in self.f.known.items() if t.crop is not None and not t.ripe and not t.watered
                   and crops[t.crop].get("grows_when", "watered") == "watered"]
        act = self.reach(p, "water", thirsty)
        return (act, "") if act is not None else (None, "nothing to water")

    def do_refill(self, p: Percept) -> tuple[Action | None, str]:
        if not p.holding_can:
            return None, "not holding the can"
        if p.can_charge is not None and p.can_charge >= p.can_size:
            return None, "the can is full"
        hours = (p.catalog.get("can") or {}).get("refill_hours")
        if hours and p.hour % 24 not in hours:
            return None, "the source gives nothing now"
        act = self.reach(p, "refill", [k for k, t in self.f.known.items() if p.catalog["tiles"][t.kind].get("source")])
        return (act, "") if act is not None else (None, "no water source known")

    def do_harvest(self, p: Percept) -> tuple[Action | None, str]:
        act = self.reach(p, "harvest", [k for k, t in self.f.known.items() if t.ripe])
        return (act, "") if act is not None else (None, "nothing ripe")

    def do_make_seeds(self, p: Percept) -> tuple[Action | None, str]:
        seeds = {spec["seeds"] for spec in p.catalog["crops"].values()}
        for name, r in (p.catalog.get("recipes") or {}).items():
            if set(r["makes"]) & seeds and all(p.inventory.get(i, 0) >= n for i, n in r["needs"].items()):
                return {"type": "craft", "recipe": name}, ""
        return None, "no harvest to make seeds from"

    def toward(self, p: Percept, pos: tuple[int, int], then: Action) -> tuple[Action | None, str]:
        if abs(pos[0] - p.x) + abs(pos[1] - p.y) == 1:
            return then, ""
        step = self.reach(p, "give", [pos])
        if step is not None and step["type"] == "move":
            return step, ""
        return None, "no way there"

    def do_ask_can(self, p: Percept) -> tuple[Action | None, str]:
        if p.holding_can:
            return None, "already holding the can"
        if p.can_holder is None or p.can_holder not in p.others:
            return None, "the can's holder is not in sight"
        return self.toward(p, p.others[p.can_holder], {"type": "wait"})

    def do_give_can(self, p: Percept) -> tuple[Action | None, str]:
        if not p.holding_can:
            return None, "not holding the can"
        if not p.others:
            return None, "no one in sight"
        name, pos = min(p.others.items(), key=lambda kv: abs(kv[1][0] - p.x) + abs(kv[1][1] - p.y))
        return self.toward(p, pos, {"type": "give", "to": name, "item": "can"})

    def do_explore(self, p: Percept) -> tuple[Action | None, str]:
        tiles = p.catalog["tiles"]
        lore = [k for k, t in self.f.known.items() if tiles[t.kind].get("lore") and k not in self.examined]
        act = self.reach(p, "examine", lore)
        if act is not None:
            if act["type"] == "examine":
                dx, dy = next(d for d, name in STEPS.items() if name == act["dir"])
                self.examined.add((p.x + dx, p.y + dy))
            return act, ""
        # The frontier: walkable tiles known, next to a tile not yet seen, not stood on yet.
        known = self.f.known
        frontier = [k for k, t in known.items() if tiles[t.kind].get("walk") and k not in self.stood
                    and any((k[0] + dx, k[1] + dy) not in known and k[0] + dx >= 0 and k[1] + dy >= 0
                            for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)))]
        step = self.reach(p, "give", frontier)
        if step is not None and step["type"] == "move":
            return step, ""
        return None, "nothing left to explore"

    def do_gather(self, p: Percept) -> tuple[Action | None, str]:
        tiles = p.catalog["tiles"]
        heaps = [k for k, t in self.f.known.items() if tiles[t.kind].get("gather")
                 and p.energy >= tiles[t.kind]["gather"].get("energy", 0)]
        act = self.reach(p, "gather", heaps)
        return (act, "") if act is not None else (None, "nothing to gather")

    def do_wait(self, p: Percept) -> tuple[Action | None, str]:
        return {"type": "wait"}, ""


class RandomIntent:
    """The floor of gate 2: a feasible intention drawn at random every hour, carried out by the same
    executor. It never speaks."""

    kind = "intent:random"

    def __init__(self, me: str, seed: int = 0) -> None:
        self.me = me
        self.ex = Executor(me)
        self.rng = random.Random(f"{seed}:{me}")
        self.last: dict[str, Any] = {}

    def decide(self, p: Percept) -> list[Action]:
        order = [i for i in INTENTIONS if i != "wait"]
        self.rng.shuffle(order)
        for intention in order + ["wait"]:
            act, why = self.ex.act(p, intention)
            if act is not None:
                self.last = {"seconds": 0.0, "parsed": True, "intention": intention, "infeasible": ""}
                return [act]
        return [{"type": "wait"}]

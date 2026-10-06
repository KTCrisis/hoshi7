"""What one agent perceives, as data: the tiles within sight, the people
within sight, what it heard or was given since its last turn. Every brain
(scripted, LLM, hybrid, human) receives this and nothing more; the text an
LLM reads is rendered from it (view.py)."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

from .events import Event, Examined, Gave, Rejected, Said
from .world import SIGHT, World



@dataclass(frozen=True)
class Seen:
    kind: str
    tilled: bool
    watered: bool
    crop: str | None
    grown: int
    ripe: bool


@dataclass(frozen=True)
class Percept:
    me: str
    tick: int
    day: int
    hour: int
    world: str
    plane: str
    loop: int
    x: int
    y: int
    energy: int
    max_energy: int
    inventory: dict[str, int]
    can_name: str
    can_size: int
    # The can: its charge is known only to whoever holds it.
    holding_can: bool
    can_charge: int | None
    can_holder: str | None
    sight: int
    tiles: dict[tuple[int, int], Seen]
    others: dict[str, tuple[int, int]]
    witnessed: list[dict[str, Any]]
    catalog: dict[str, Any] = field(repr=False)
    objective: dict[str, Any] = field(default_factory=dict)
    harvested: int = 0
    acted: bool = False
    said: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["tiles"] = [{"x": x, "y": y, **dataclasses.asdict(t)} for (x, y), t in sorted(self.tiles.items())]
        d["others"] = {k: list(v) for k, v in self.others.items()}
        d.pop("catalog")
        return d


def witnessed(log: list[Event], me: str, since: int) -> list[dict[str, Any]]:
    """The events this agent took part in or heard, from log index `since`
    (a runner passes the log length at the agent's previous turn)."""
    out = []
    for e in log[since:]:
        match e:
            case Said() if me in e.hearers or e.agent == me:
                out.append(e.to_dict())
            case Gave() if e.to == me or e.agent == me:
                out.append(e.to_dict())
            case Rejected() | Examined() if e.agent == me:
                out.append(e.to_dict())
    return out


def current_hour(w: World) -> int:
    """Log index of the first event of the current hour."""
    tick = w.state.tick
    return next((i for i, e in enumerate(w.log) if e.tick >= tick), len(w.log))


def perceive(w: World, me: str, since: int | None = None, sight: int = SIGHT) -> Percept:
    s = w.state
    a = s.agents[me]
    tiles = {}
    for y in range(max(0, a.y - sight), min(s.height, a.y + sight + 1)):
        for x in range(max(0, a.x - sight), min(s.width, a.x + sight + 1)):
            t = s.tile(x, y)
            ripe = t.crop is not None and t.grown >= s.crops[t.crop]["days"]
            tiles[(x, y)] = Seen(t.kind, t.tilled, t.watered, t.crop, t.grown, ripe)
    others = {
        b.id: (b.x, b.y) for b in s.agents.values()
        if b.id != me and abs(b.x - a.x) <= sight and abs(b.y - a.y) <= sight
    }
    holder = s.can_holder if s.can_holder == me or s.can_holder in others else None
    return Percept(
        me=me, tick=s.tick, day=s.day, hour=s.hour, world=s.world, plane=s.plane, loop=s.loop,
        x=a.x, y=a.y, energy=a.energy, max_energy=s.max_energy, inventory=dict(a.inventory),
        can_name=s.can.get("name", "can"), can_size=s.can.get("size", 0),
        holding_can=s.can_holder == me, can_charge=s.can_charge if s.can_holder == me else None,
        can_holder=holder, sight=sight, tiles=tiles, others=others,
        witnessed=witnessed(w.log, me, current_hour(w) if since is None else since),
        catalog={"tiles": s.tiles, "crops": s.crops, "recipes": s.recipes, "lore": s.lore, "can": s.can, "clock": s.clock},
        objective=dict(s.objective), harvested=s.harvested.get(s.objective.get("harvest", ""), 0),
        acted=a.acted, said=a.said,
    )

"""The world: rules that turn an action into events, and apply, which folds
an event into the state. The state never changes any other way, so a log of
events replays into the same world.

The engine knows only kinds of ground (walkable, soil, a source to refill
from, something to gather, something to examine); each world file names them
and says what they give, so a cyber rooftop, a Belle Epoque conservatory and
an asteroid station run on the same rules.
"""

from __future__ import annotations

import copy
import dataclasses
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .events import (
    Created, Crafted, DayStarted, Ended, Event, Examined, Gathered, Gave,
    Harvested, HourPassed, Joined, Moved, Planted, Refilled, Rejected, Said,
    Tilled, Waited, Watered,
)

DAY_START = 6
# 2 am the next morning: whoever is still up passes out.
DAY_END = 26
MOVE_RANGE = 5
SAY_RADIUS = 6
SAY_CHARS = 280
# How far an agent sees, in tiles each way (a square): the percept's range, and what a refusal may name.
SIGHT = 5
# Actions that are work: with a clock, possible only during its work hours.
WORK = frozenset({"till", "plant", "water", "harvest", "refill", "gather", "craft"})
DIRS = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0), "here": (0, 0)}
COST = {"till": 2, "water": 1}


@dataclass
class Tile:
    kind: str
    tilled: bool = False
    watered: bool = False
    crop: str | None = None
    grown: int = 0


@dataclass
class Agent:
    id: str
    x: int
    y: int
    energy: int
    inventory: dict[str, int]
    acted: bool = False
    said: bool = False


@dataclass
class State:
    world: str = ""
    plane: str = ""
    loop: int = 0
    seed: int = 0
    grid: list[list[Tile]] = field(default_factory=list)
    tiles: dict[str, Any] = field(default_factory=dict)
    crops: dict[str, Any] = field(default_factory=dict)
    recipes: dict[str, Any] = field(default_factory=dict)
    lore: dict[str, Any] = field(default_factory=dict)
    can: dict[str, Any] = field(default_factory=dict)
    clock: dict[str, Any] = field(default_factory=dict)
    objective: dict[str, Any] = field(default_factory=dict)
    max_energy: int = 0
    spawns: list[dict[str, Any]] = field(default_factory=list)
    agents: dict[str, Agent] = field(default_factory=dict)
    # The can: who holds it, how much it still pours.
    can_holder: str | None = None
    can_charge: int = 0
    tick: int = 0
    day: int = 1
    hour: int = DAY_START
    harvested: dict[str, int] = field(default_factory=dict)
    outcome: str | None = None

    @property
    def width(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @property
    def height(self) -> int:
        return len(self.grid)

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile(self, x: int, y: int) -> Tile:
        return self.grid[y][x]

    def spec(self, x: int, y: int) -> dict[str, Any]:
        return self.tiles[self.tile(x, y).kind]

    def occupant(self, x: int, y: int) -> str | None:
        return next((a.id for a in self.agents.values() if (a.x, a.y) == (x, y)), None)

    def walkable(self, x: int, y: int) -> bool:
        return self.inside(x, y) and bool(self.spec(x, y).get("walk")) and self.occupant(x, y) is None


def apply(s: State, e: Event) -> None:
    """Fold one event into the state; the only place the state changes."""
    match e:
        case Created():
            s.world, s.plane, s.loop, s.seed = e.world, e.plane, e.loop, e.seed
            s.grid = [[Tile(c) for c in row] for row in e.rows]
            s.tiles, s.crops, s.recipes, s.lore = e.tiles, e.crops, e.recipes, e.lore
            s.can, s.objective, s.max_energy, s.spawns = e.can, e.objective, e.max_energy, e.spawns
            s.clock = dict(e.clock)
            s.can_charge = e.can.get("size", 0)
        case Joined():
            s.agents[e.agent] = Agent(e.agent, e.x, e.y, s.max_energy, dict(e.inventory))
            if "can" in e.tools:
                s.can_holder = e.agent
        case Moved():
            a = s.agents[e.agent]
            a.x, a.y = e.x, e.y
            a.acted = True
        case Tilled():
            s.tile(e.x, e.y).tilled = True
            spend(s, e.agent, COST["till"])
        case Watered():
            s.tile(e.x, e.y).watered = True
            s.can_charge -= 1
            spend(s, e.agent, COST["water"])
        case Refilled():
            s.can_charge = s.can["size"]
            s.agents[e.agent].acted = True
        case Planted():
            t = s.tile(e.x, e.y)
            t.crop, t.grown = e.crop, 0
            take(s.agents[e.agent], s.crops[e.crop]["seeds"], 1)
            s.agents[e.agent].acted = True
        case Harvested():
            t = s.tile(e.x, e.y)
            t.crop, t.grown = None, 0
            give(s.agents[e.agent], e.crop, e.qty)
            s.harvested[e.crop] = s.harvested.get(e.crop, 0) + e.qty
            s.agents[e.agent].acted = True
        case Gathered():
            spec = s.spec(e.x, e.y)["gather"]
            s.tile(e.x, e.y).kind = spec["becomes"]
            for item, n in e.yields.items():
                give(s.agents[e.agent], item, n)
            spend(s, e.agent, spec.get("energy", 0))
        case Examined():
            s.agents[e.agent].acted = True
        case Crafted():
            a = s.agents[e.agent]
            r = s.recipes[e.recipe]
            for item, n in r["needs"].items():
                take(a, item, n)
            for item, n in r["makes"].items():
                give(a, item, n)
            a.acted = True
        case Gave():
            if e.item == "can":
                s.can_holder = e.to
            else:
                take(s.agents[e.agent], e.item, e.qty)
                give(s.agents[e.to], e.item, e.qty)
            s.agents[e.agent].acted = True
        case Said():
            s.agents[e.agent].said = True
        case Waited():
            s.agents[e.agent].acted = True
        case Rejected():
            pass
        case HourPassed():
            s.tick, s.day, s.hour = e.tick, e.day, e.hour
            for a in s.agents.values():
                a.acted = a.said = False
        case DayStarted():
            s.tick, s.day, s.hour = e.tick, e.day, DAY_START
            for row in s.grid:
                for t in row:
                    # A crop grows on watered days, or on dry days if its world says `grows_when: dry`.
                    if t.crop is not None and t.watered == (s.crops[t.crop].get("grows_when", "watered") == "watered"):
                        t.grown += 1
                    t.watered = False
            for a in s.agents.values():
                a.energy = s.max_energy
                a.acted = a.said = False
        case Ended():
            s.outcome = e.outcome
        case _:
            raise TypeError(f"unknown event {type(e).__name__}")


def spend(s: State, agent: str, energy: int) -> None:
    a = s.agents[agent]
    a.energy -= energy
    a.acted = True


def give(a: Agent, item: str, n: int) -> None:
    a.inventory[item] = a.inventory.get(item, 0) + n


def take(a: Agent, item: str, n: int) -> None:
    left = a.inventory.get(item, 0) - n
    if left > 0:
        a.inventory[item] = left
    else:
        a.inventory.pop(item, None)


class Refusal(Exception):
    pass


def no_can(s: State, a: Agent) -> Refusal:
    """The refusal for an act that needs the can, saying who holds it (if within sight) and that only the
    holder can give it. "not holding the can" alone left a model playing give, the only verb about the can,
    to get it: twenty-four times in a row (Mistral, 2026-10-06)."""
    b = s.agents.get(s.can_holder or "")
    if b is None:
        return Refusal("not holding the can")
    who = b.id if max(abs(b.x - a.x), abs(b.y - a.y)) <= SIGHT else "someone out of sight"
    return Refusal(f"not holding the can: {who} holds it, and only the holder can give it")


class World:
    """A state and the log that made it."""

    def __init__(self) -> None:
        self.state = State()
        self.log: list[Event] = []

    @classmethod
    def create(cls, spec: dict[str, Any], *, loop: int = 1, seed: int = 0) -> World:
        w = cls()
        rows = [r for r in spec["map"].splitlines() if r]
        if len({len(r) for r in rows}) != 1:
            raise ValueError("map rows must have the same width")
        unknown = {c for r in rows for c in r} - spec["tiles"].keys()
        if unknown:
            raise ValueError(f"map uses undefined tiles: {sorted(unknown)}")
        w.emit(Created(
            0, spec["name"], spec["plane"], loop, seed, rows, spec["tiles"],
            spec.get("crops", {}), spec.get("recipes", {}), spec.get("lore", {}),
            spec.get("can", {}), spec["objective"], spec["max_energy"], spec["spawns"], spec.get("clock", {}),
        ))
        return w

    @classmethod
    def replay(cls, events: list[Event]) -> World:
        w = cls()
        for e in events:
            w.emit(e)
        return w

    def emit(self, e: Event) -> Event:
        apply(self.state, e)
        self.log.append(e)
        return e

    def join(self, agent: str) -> Joined:
        s = self.state
        if agent in s.agents:
            raise ValueError(f"{agent} is already here")
        if len(s.agents) >= len(s.spawns):
            raise ValueError("no spawn left")
        spawn = s.spawns[len(s.agents)]
        x, y = spawn["at"]
        e = Joined(s.tick, agent, x, y, dict(spawn.get("inventory", {})), list(spawn.get("tools", [])))
        self.emit(e)
        return e

    def act(self, agent: str, action: dict[str, Any]) -> list[Event]:
        """One action for one agent. A refused action is an event too, so
        the log keeps what was tried as well as what happened."""
        s = self.state
        kind = str(action.get("type", ""))
        try:
            if s.outcome is not None:
                raise Refusal(f"the world has ended ({s.outcome})")
            a = s.agents.get(agent)
            if a is None:
                raise Refusal("not in this world")
            if kind == "say":
                if a.said:
                    raise Refusal("already spoke this hour")
            elif a.acted:
                raise Refusal("already acted this hour")
            rule = RULES.get(kind)
            if rule is None:
                raise Refusal(f"unknown action {kind!r}")
            work = s.clock.get("work")
            if work and kind in WORK and not work[0] <= s.hour % 24 < work[1]:
                raise Refusal(f"it is night: work stops at {work[1]:02d}:00 and resumes at {work[0]:02d}:00")
            events = rule(s, a, action)
        except Refusal as r:
            return [self.emit(Rejected(s.tick, agent, kind, str(r)))]
        except KeyError as err:  # str(KeyError) is "'crop'": a model read it as nothing (2026-10-06)
            return [self.emit(Rejected(s.tick, agent, kind, f"malformed action: {kind} needs {err.args[0]!r}"))]
        except (TypeError, ValueError) as err:
            return [self.emit(Rejected(s.tick, agent, kind, f"malformed action: {err}"))]
        out = [self.emit(e) for e in events]
        if any(isinstance(e, Harvested) for e in out) and won(s):
            out.append(self.emit(Ended(s.tick, "won")))
        return out

    def advance(self) -> list[Event]:
        """One hour passes; past 2 am a new day starts."""
        s = self.state
        if s.outcome is not None:
            return []
        if s.hour + 1 < DAY_END:
            return [self.emit(HourPassed(s.tick + 1, s.day, s.hour + 1))]
        out = [self.emit(DayStarted(s.tick + 1, s.day + 1))]
        if s.day > s.objective["by_day"]:
            out.append(self.emit(Ended(s.tick, "lost")))
        return out


def won(s: State) -> bool:
    o = s.objective
    return s.harvested.get(o["harvest"], 0) >= o["count"]


def target(s: State, a: Agent, action: dict[str, Any]) -> tuple[int, int]:
    if "x" in action and "y" in action:  # the tile by its coordinates: one's own or one next to it
        x, y = int(action["x"]), int(action["y"])
        steps = abs(x - a.x) + abs(y - a.y)
        if steps > 1:
            raise Refusal(f"({x},{y}) is {steps} steps away; act on your tile or one next to it")
        if not s.inside(x, y):
            raise Refusal("outside the world")
        return x, y
    if "x" in action or "y" in action:
        raise Refusal("give both x and y of the tile")
    # No tile named: refused, not read as "here" (until 2026-10-06 a model that left out x, y acted
    # on its own tile without knowing it).
    if "dir" not in action:
        raise Refusal("which tile? (x and y, or dir)")
    d = action["dir"]
    if d not in DIRS:
        raise Refusal(f"unknown direction {d!r}")
    dx, dy = DIRS[d]
    x, y = a.x + dx, a.y + dy
    if not s.inside(x, y):
        raise Refusal("outside the world")
    return x, y


def need_energy(a: Agent, n: int) -> None:
    if a.energy < n:
        raise Refusal(f"too tired ({a.energy} energy, needs {n})")


def path_length(s: State, a: Agent, goal: tuple[int, int]) -> int | None:
    seen = {(a.x, a.y)}
    q = deque([((a.x, a.y), 0)])
    while q:
        (x, y), n = q.popleft()
        if (x, y) == goal:
            return n
        if n == MOVE_RANGE:
            continue
        for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)):
            p = (x + dx, y + dy)
            if p not in seen and s.walkable(*p):
                seen.add(p)
                q.append((p, n + 1))
    return None


def do_move(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    goal = (int(act["x"]), int(act["y"]))
    if goal == (a.x, a.y):
        raise Refusal("already there")
    if not s.walkable(*goal):
        raise Refusal("cannot stand there")
    if path_length(s, a, goal) is None:
        raise Refusal(f"no path within {MOVE_RANGE} steps")
    return [Moved(s.tick, a.id, *goal)]


STEPS4 = ((0, -1), (0, 1), (1, 0), (-1, 0))


def places(s: State, a: Agent, name: str) -> tuple[str, set[tuple[int, int]]] | None:
    """The tiles to stand on to be next to a named place: another agent, a tile kind (its symbol or its
    name), or the words "soil" and "source"; None if nothing on the map answers to the name."""
    key = str(name).strip().lower()
    other = next((b for b in s.agents.values() if b.id.lower() == key and b.id != a.id), None)
    if other is not None:
        return other.id, {(other.x + dx, other.y + dy) for dx, dy in STEPS4}
    kinds = {k for k, t in s.tiles.items()
             if key in (k, str(t.get("name", "")).lower())
             or (key == "soil" and t.get("soil")) or (key == "source" and t.get("source"))}
    if not kinds:
        return None
    cells = {(x, y) for y, row in enumerate(s.grid) for x, t in enumerate(row) if t.kind in kinds}
    label = key if key in ("soil", "source") else s.tiles[sorted(kinds)[0]].get("name", key)
    return label, {(x + dx, y + dy) for x, y in cells for dx, dy in STEPS4}


def route(s: State, a: Agent, goals: set[tuple[int, int]]) -> list[tuple[int, int]] | None:
    """Shortest walkable path from the agent to the nearest goal tile, the whole map, start excluded."""
    prev: dict[tuple[int, int], tuple[int, int] | None] = {(a.x, a.y): None}
    q = deque([(a.x, a.y)])
    while q:
        p = q.popleft()
        if p in goals and p != (a.x, a.y):
            out = []
            while p != (a.x, a.y):
                out.append(p)
                p = prev[p]  # type: ignore[assignment]
            return out[::-1]
        for dx, dy in STEPS4:
            n = (p[0] + dx, p[1] + dy)
            if n not in prev and s.walkable(*n):
                prev[n] = p
                q.append(n)
    return None


def do_go(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    """Walk toward a named place, or toward a given tile (x, y), up to MOVE_RANGE steps this hour,
    stopping next to it; the engine finds the way, so an agent no longer has to read the grid to reach
    a place it cannot see. A tile is what a brain sends for a place it remembers: the way leads there,
    not to the nearest place of that kind, which it may never have seen."""
    if "x" in act and "y" in act:
        x, y = int(act["x"]), int(act["y"])
        if not s.inside(x, y):
            raise Refusal("outside the world")
        label, goals = f"({x},{y})", {(x + dx, y + dy) for dx, dy in STEPS4}
        if (a.x, a.y) == (x, y):  # standing on it is being there; route() would step off it
            raise Refusal(f"already at {label}")
    else:
        found = places(s, a, act["to"])
        if found is None:
            raise Refusal(f"no place called {act['to']!r}")
        label, goals = found
    if (a.x, a.y) in goals:
        raise Refusal(f"already next to {label}")
    path = route(s, a, goals)
    if path is None:
        raise Refusal(f"no way to {label}")
    x, y = path[min(len(path), MOVE_RANGE) - 1]
    return [Moved(s.tick, a.id, x, y)]


def do_till(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    x, y = target(s, a, act)
    if not s.spec(x, y).get("soil"):
        raise Refusal("not soil")
    if s.tile(x, y).tilled:
        raise Refusal("already tilled")
    need_energy(a, COST["till"])
    return [Tilled(s.tick, a.id, x, y)]


def do_water(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    x, y = target(s, a, act)
    if s.can_holder != a.id:
        raise no_can(s, a)
    if s.can_charge <= 0:
        raise Refusal("the can is empty")
    t = s.tile(x, y)
    if not t.tilled:
        raise Refusal("not tilled")
    if t.watered:
        raise Refusal("already watered")
    need_energy(a, COST["water"])
    return [Watered(s.tick, a.id, x, y)]


def do_refill(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    if s.can_holder != a.id:
        raise no_can(s, a)
    near = any(
        s.inside(a.x + dx, a.y + dy) and s.spec(a.x + dx, a.y + dy).get("source")
        for dx, dy in DIRS.values()
    )
    if not near:
        raise Refusal("no source within reach")
    hours = s.can.get("refill_hours")
    if hours and s.hour % 24 not in hours:
        raise Refusal("the source gives nothing now")
    return [Refilled(s.tick, a.id)]


def do_plant(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    x, y = target(s, a, act)
    crop = act["crop"]
    if crop not in s.crops:
        raise Refusal(f"unknown crop {crop!r}")
    if a.inventory.get(s.crops[crop]["seeds"], 0) < 1:
        raise Refusal(f"no {s.crops[crop]['seeds']}")
    t = s.tile(x, y)
    if not t.tilled:
        raise Refusal("not tilled")
    if t.crop is not None:
        raise Refusal("something grows there already")
    return [Planted(s.tick, a.id, x, y, crop)]


def do_harvest(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    x, y = target(s, a, act)
    t = s.tile(x, y)
    if t.crop is None:
        raise Refusal("nothing grows there")
    days = s.crops[t.crop]["days"]
    if t.grown < days:
        raise Refusal(f"not ripe ({t.grown}/{days} days)")
    return [Harvested(s.tick, a.id, x, y, t.crop, s.crops[t.crop].get("yield", 1))]


def do_gather(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    x, y = target(s, a, act)
    spec = s.spec(x, y).get("gather")
    if spec is None:
        raise Refusal("nothing to gather")
    need_energy(a, spec.get("energy", 0))
    return [Gathered(s.tick, a.id, x, y, dict(spec["yields"]))]


def do_examine(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    x, y = target(s, a, act)
    lore = s.spec(x, y).get("lore")
    if lore is None:
        raise Refusal("nothing to learn there")
    return [Examined(s.tick, a.id, x, y, lore)]


def do_craft(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    name = act["recipe"]
    r = s.recipes.get(name)
    if r is None:
        raise Refusal(f"unknown recipe {name!r}")
    short = {i: n for i, n in r["needs"].items() if a.inventory.get(i, 0) < n}
    if short:
        raise Refusal(f"missing {short}")
    return [Crafted(s.tick, a.id, name)]


def do_give(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    to, item, qty = act["to"], act["item"], int(act.get("qty", 1))
    # Names are matched without case: a model writes "Ben" for ben, and the can never changed hands.
    to = next((k for k in s.agents if k.lower() == str(to).strip().lower()), to)
    b = s.agents.get(to)
    if b is None or to == a.id:
        raise Refusal(f"no one called {to!r} to give to")
    if abs(a.x - b.x) + abs(a.y - b.y) > 1:
        raise Refusal(f"{to} is out of reach")
    if item == "can":
        if s.can_holder != a.id:
            raise no_can(s, a)
        qty = 1
    elif qty < 1 or a.inventory.get(item, 0) < qty:
        raise Refusal(f"not enough {item}")
    return [Gave(s.tick, a.id, to, item, qty)]


def do_say(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    text = str(act["text"]).strip()[:SAY_CHARS]
    if not text:
        raise Refusal("nothing to say")
    hearers = sorted(
        b.id for b in s.agents.values()
        if b.id != a.id and abs(a.x - b.x) + abs(a.y - b.y) <= SAY_RADIUS
    )
    return [Said(s.tick, a.id, text, hearers)]


def do_wait(s: State, a: Agent, act: dict[str, Any]) -> list[Event]:
    return [Waited(s.tick, a.id)]


RULES = {
    "move": do_move, "go": do_go, "till": do_till, "water": do_water, "refill": do_refill,
    "plant": do_plant, "harvest": do_harvest, "gather": do_gather,
    "examine": do_examine, "craft": do_craft, "give": do_give, "say": do_say,
    "wait": do_wait,
}


def snapshot(s: State) -> dict[str, Any]:
    """The state as plain data, for comparison and for clients."""
    return copy.deepcopy(dataclasses.asdict(s))

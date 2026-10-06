"""The world's events: everything that happens is one of these, and the state
is what you get by applying them in order (see world.apply)."""

from __future__ import annotations

import dataclasses
import typing
from dataclasses import dataclass
from typing import Any

EVENTS: dict[str, type[Event]] = {}


@dataclass(frozen=True)
class Event:
    tick: int

    def to_dict(self) -> dict[str, Any]:
        return {"type": type(self).__name__, **dataclasses.asdict(self)}


def event(cls: type) -> type:
    cls = dataclass(frozen=True)(cls)
    EVENTS[cls.__name__] = cls
    return cls


def from_dict(d: dict[str, Any]) -> Event:
    d = dict(d)
    cls = EVENTS[d.pop("type")]
    return cls(**d)


def hints(cls: type) -> dict[str, Any]:
    return typing.get_type_hints(cls)


# The world itself: its map and catalog travel in the first event, so a log
# replays alone.
@event
class Created(Event):
    world: str
    plane: str
    loop: int
    seed: int
    rows: list[str]
    tiles: dict[str, Any]
    crops: dict[str, Any]
    recipes: dict[str, Any]
    lore: dict[str, Any]
    can: dict[str, Any]
    objective: dict[str, Any]
    max_energy: int
    spawns: list[dict[str, Any]]
    # optional: {"work": [7, 19]} = the hours when work is possible (absent: any hour)
    clock: dict[str, Any] = dataclasses.field(default_factory=dict)


@event
class Joined(Event):
    agent: str
    x: int
    y: int
    inventory: dict[str, int]
    tools: list[str]


@event
class Moved(Event):
    agent: str
    x: int
    y: int


@event
class Tilled(Event):
    agent: str
    x: int
    y: int


@event
class Watered(Event):
    agent: str
    x: int
    y: int


@event
class Refilled(Event):
    agent: str


@event
class Planted(Event):
    agent: str
    x: int
    y: int
    crop: str


@event
class Harvested(Event):
    agent: str
    x: int
    y: int
    crop: str
    qty: int


@event
class Gathered(Event):
    agent: str
    x: int
    y: int
    yields: dict[str, int]


@event
class Examined(Event):
    agent: str
    x: int
    y: int
    lore: str


@event
class Crafted(Event):
    agent: str
    recipe: str


@event
class Gave(Event):
    agent: str
    to: str
    item: str
    qty: int


@event
class Said(Event):
    agent: str
    text: str
    hearers: list[str]


@event
class Waited(Event):
    agent: str


@event
class Rejected(Event):
    agent: str
    action: str
    reason: str


@event
class HourPassed(Event):
    day: int
    hour: int


@event
class DayStarted(Event):
    day: int


@event
class Ended(Event):
    outcome: str

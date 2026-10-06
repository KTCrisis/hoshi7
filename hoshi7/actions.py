"""The action catalog: what an agent may do, its parameters and its cost.
The same table feeds the agent's prompt, the MCP tools (later) and the
documentation; world.RULES must cover exactly these names."""

from __future__ import annotations

from typing import Any

from .world import COST, DIRS, MOVE_RANGE, SAY_CHARS, SAY_RADIUS

DIR = {"type": "string", "enum": list(DIRS), "description": "n, s, e, w, or here (the tile you stand on)"}
# The actions that point at a tile take a direction, or the tile's coordinates (2026-10-06): an agent
# that reads the field in coordinates no longer has to turn them into a direction, which it got wrong.
AIMED = ("till", "plant", "water", "harvest", "gather", "examine")

CATALOG: dict[str, dict[str, Any]] = {
    "move": {
        "doc": f"Walk to a free walkable tile up to {MOVE_RANGE} steps away.",
        "params": {"x": {"type": "integer"}, "y": {"type": "integer"}},
        "uses_turn": True,
        "energy": 0,
    },
    "go": {
        "doc": (f"Walk toward a named place, even out of sight: another agent's name, a tile from the legend "
                f"(its name), or soil, or source; up to {MOVE_RANGE} steps this hour, stopping next to it. "
                "Repeat it to keep going."),
        "params": {"to": {"type": "string"}},
        "uses_turn": True,
        "energy": 0,
    },
    "till": {
        "doc": "Till a soil tile so something can be planted there.",
        "params": {"dir": DIR},
        "uses_turn": True,
        "energy": COST["till"],
    },
    "plant": {
        "doc": "Plant a crop on a tilled, empty tile; uses one of its seeds.",
        "params": {"dir": DIR, "crop": {"type": "string"}},
        "uses_turn": True,
        "energy": 0,
    },
    "water": {
        "doc": "Water a tilled tile; needs the can, uses one charge. Crops grow only on watered days.",
        "params": {"dir": DIR},
        "uses_turn": True,
        "energy": COST["water"],
    },
    "refill": {
        "doc": "Refill the can next to a source.",
        "params": {},
        "uses_turn": True,
        "energy": 0,
    },
    "harvest": {
        "doc": "Harvest a ripe crop.",
        "params": {"dir": DIR},
        "uses_turn": True,
        "energy": 0,
    },
    "gather": {
        "doc": "Gather a resource tile (its yield and energy cost depend on the world).",
        "params": {"dir": DIR},
        "uses_turn": True,
        "energy": "per tile",
    },
    "examine": {
        "doc": "Examine something that can be read or studied; what you learn may matter later.",
        "params": {"dir": DIR},
        "uses_turn": True,
        "energy": 0,
    },
    "craft": {
        "doc": "Turn items you carry into another, following a recipe.",
        "params": {"recipe": {"type": "string"}},
        "uses_turn": True,
        "energy": 0,
    },
    "give": {
        "doc": "Give items, or the can, to someone next to you.",
        "params": {"to": {"type": "string"}, "item": {"type": "string"}, "qty": {"type": "integer", "default": 1}},
        "uses_turn": True,
        "energy": 0,
    },
    "say": {
        "doc": f"Speak; heard within {SAY_RADIUS} tiles, {SAY_CHARS} characters at most. Free, once per hour.",
        "params": {"text": {"type": "string"}},
        "uses_turn": False,
        "energy": 0,
    },
    "wait": {
        "doc": "Let the hour pass.",
        "params": {},
        "uses_turn": True,
        "energy": 0,
    },
}


for _name in AIMED:
    CATALOG[_name]["params"] = {**CATALOG[_name]["params"], "x": {"type": "integer"}, "y": {"type": "integer"}}


def describe(exclude: frozenset[str] = frozenset(), coords: bool = False) -> str:
    """The catalog as text, for a prompt. `coords`: the aimed actions take x, y instead of dir."""
    lines = []
    for name, a in CATALOG.items():
        if name in exclude:
            continue
        ps = list(a["params"])
        if name in AIMED:
            ps = [p for p in ps if p != "dir"] if coords else [p for p in ps if p not in ("x", "y")]
            if coords:
                ps = ["x", "y"] + [p for p in ps if p not in ("x", "y")]
        params = ", ".join(ps) or "-"
        cost = a["energy"] if a["energy"] else "free"
        lines.append(f"- {name}({params}): {a['doc']} Energy: {cost}.")
    if coords:
        lines.append("x, y of till, plant, water, harvest, gather, examine: the tile you act on, the one you stand on "
                     "or one of the four next to it.")
        lines.append("One action per hour, plus one say. Example: {\"type\": \"till\", \"x\": 6, \"y\": 4}")
    else:
        lines.append("One action per hour, plus one say. Example: {\"type\": \"till\", \"dir\": \"e\"}")
    return "\n".join(lines)

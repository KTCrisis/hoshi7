"""A percept as text, for an LLM. The world holds no prose; sentences are
made here, from what the agent perceives and nothing else."""

from __future__ import annotations

from .percept import Percept, perceive
from .world import DIRS, World


def label(item: str) -> str:
    return item.replace("_", " ")


def cell(p: Percept, x: int, y: int) -> str:
    if (x, y) == (p.x, p.y):
        return "@"
    who = next((o for o, pos in p.others.items() if pos == (x, y)), None)
    if who is not None:
        return who[0].upper()
    t = p.tiles[(x, y)]
    if t.crop is not None:
        return "!" if t.ripe else str(min(t.grown, 9))
    if t.tilled:
        return "*" if t.watered else "="
    return t.kind


def grid(p: Percept) -> list[str]:
    xs = sorted({x for x, _ in p.tiles})
    ys = sorted({y for _, y in p.tiles})
    lines = ["    " + "".join(str(x % 10) for x in xs)]
    lines += [f"{y:3d} " + "".join(cell(p, x, y) for x in xs) for y in ys]
    return lines


def describe_tile(p: Percept, x: int, y: int) -> str:
    """One tile in words: what it is and what grows there."""
    who = next((o for o, pos in p.others.items() if pos == (x, y)), None)
    if who is not None and (x, y) != (p.x, p.y):
        return who
    t = p.tiles.get((x, y))
    if t is None:
        return "nothing (edge)"
    spec = p.catalog["tiles"][t.kind]
    words = [spec["name"]]
    if spec.get("soil") and not t.tilled:
        words.append("soil, untilled")
    if t.tilled:
        words.append("tilled, watered" if t.watered else "tilled, dry")
    if t.crop is not None:
        words.append(f"{t.crop} ripe" if t.ripe else f"{t.crop} grown {t.grown} day(s)")
    return ", ".join(words)


def adjacent(p: Percept) -> str:
    """What the directions of the actions reach, so no one counts on the grid."""
    return "; ".join(f"{d}: {describe_tile(p, p.x + dx, p.y + dy)}" for d, (dx, dy) in DIRS.items())


def reach(p: Percept) -> list[str]:
    """Where each agent in sight is, and whether a give would reach them: only n, s, e or w count,
    and two cooperative agents standing on a diagonal never managed to pass the can."""
    out = []
    for name, (x, y) in sorted(p.others.items()):
        d = abs(x - p.x) + abs(y - p.y)
        if d == 1:
            out.append(f"{name} is at ({x},{y}), next to you: you can give to {name}.")
        else:
            out.append(f"{name} is at ({x},{y}), {d} steps away: to give, stand on a tile n, s, e or w of {name} (not diagonal).")
    return out


def where(p: Percept, x: int, y: int) -> str:
    """A tile relative to the agent, in steps, so no one counts on a drawn grid."""
    dx, dy = x - p.x, y - p.y
    if (dx, dy) == (0, 0):
        return "where you stand"
    if abs(dx) + abs(dy) == 1:
        return "next to you, " + {(1, 0): "e", (-1, 0): "w", (0, 1): "s", (0, -1): "n"}[(dx, dy)]
    parts = []
    if dx:
        parts.append(f"{abs(dx)} {'east' if dx > 0 else 'west'}")
    if dy:
        parts.append(f"{abs(dy)} {'south' if dy > 0 else 'north'}")
    return " and ".join(parts)


def space(p: Percept) -> list[str]:
    """What is around the agent, in words and coordinates (stage 6): the nearest untilled soil, the
    tended tiles, the water source, the other things worth a visit; replaces the drawn grid."""
    dist = lambda xy: abs(xy[0] - p.x) + abs(xy[1] - p.y)  # noqa: E731
    tiles = p.catalog["tiles"]
    lines = [f"You are at ({p.x},{p.y}); you see {p.sight} tiles around you."]
    soil = sorted((xy for xy, t in p.tiles.items() if tiles[t.kind].get("soil") and not t.tilled and t.crop is None), key=dist)
    if soil:
        lines.append("Untilled soil nearest: " + "; ".join(f"({x},{y}) {where(p, x, y)}" for x, y in soil[:3]) + ".")
    else:
        lines.append("No untilled soil in sight (go to soil).")
    tended = sorted((xy for xy, t in p.tiles.items() if t.tilled or t.crop is not None), key=dist)
    for x, y in tended[:12]:
        lines.append(f"Tended: ({x},{y}) {describe_tile(p, x, y)}, {where(p, x, y)}.")
    src = sorted((xy for xy, t in p.tiles.items() if tiles[t.kind].get("source")), key=dist)
    if src:
        x, y = src[0]
        lines.append(f"Water source: {tiles[p.tiles[(x, y)].kind]['name']} at ({x},{y}), {where(p, x, y)}; refill standing next to it.")
    else:
        lines.append("No water source in sight (go to source).")
    seen_kinds: set[str] = set()
    for xy in sorted(p.tiles, key=dist):
        t = p.tiles[xy]
        spec = tiles[t.kind]
        if (spec.get("gather") or spec.get("lore")) and t.kind not in seen_kinds:
            seen_kinds.add(t.kind)
            verb = "gather" if spec.get("gather") else "examine"
            lines.append(f"{spec['name'].capitalize()} ({verb}) at ({xy[0]},{xy[1]}), {where(p, *xy)}.")
    return lines


def untilled_step(p: Percept) -> str | None:
    """Where to stand to till next: a free tile beside the nearest untilled soil in sight. "go to soil"
    alone led beside soil already tilled, so the list of stage 7 ran into a dead end (2026-10-06)."""
    tiles = p.catalog["tiles"]
    dist = lambda xy: abs(xy[0] - p.x) + abs(xy[1] - p.y)  # noqa: E731
    taken = set(p.others.values())
    for x, y in sorted((xy for xy, t in p.tiles.items() if tiles[t.kind].get("soil") and not t.tilled and t.crop is None), key=dist):
        stands = [(x + dx, y + dy) for dx, dy in DIRS.values() if (dx, dy) != (0, 0)]
        stands = [xy for xy in stands if xy in p.tiles and tiles[p.tiles[xy].kind].get("walk") and xy not in taken]
        if stands:
            sx, sy = min(stands, key=dist)
            return f"move to ({sx},{sy}), next to untilled soil at ({x},{y})"
    return None


def affordances(p: Percept) -> str:
    """The useful actions possible this hour (stage 7), computed from the percept: the model chooses
    among them instead of guessing which tile is where. This hands the rules to the agent: stage 7 is a
    comparison arm (performance with the useful actions written for it), not the discovery harness."""
    tiles = p.catalog["tiles"]
    seeds = {c: v["seeds"] for c, v in p.catalog["crops"].items() if p.inventory.get(v["seeds"], 0) > 0}
    out: list[str] = []
    for d, (dx, dy) in DIRS.items():
        t = p.tiles.get((p.x + dx, p.y + dy))
        if t is None:
            continue
        spec = tiles[t.kind]
        if spec.get("soil") and not t.tilled and t.crop is None:
            out.append(f"till {d}")
        if t.tilled and t.crop is None:
            out += [f"plant {d} {c}" for c in seeds]
        wet = p.catalog["crops"].get(t.crop or "", {}).get("grows_when", "watered") == "watered"
        if t.crop is not None and wet and not t.ripe and not t.watered and p.holding_can and (p.can_charge or 0) > 0:
            out.append(f"water {d}")
        if t.ripe:
            out.append(f"harvest {d}")
        hours = (p.catalog.get("can") or {}).get("refill_hours")
        if (spec.get("source") and p.holding_can and (p.can_charge or 0) < p.can_size and "refill" not in out
                and (not hours or p.hour % 24 in hours)):
            out.append("refill")
        if spec.get("gather"):
            out.append(f"gather {d}")
        if spec.get("lore"):
            out.append(f"examine {d}")
    for name, (x, y) in sorted(p.others.items()):
        if abs(x - p.x) + abs(y - p.y) == 1 and p.holding_can:
            out.append(f"give can to {name}")
    for name, r in (p.catalog.get("recipes") or {}).items():
        if all(p.inventory.get(i, 0) >= n for i, n in r["needs"].items()):
            out.append(f"craft {name}")
    if not any(a.startswith(("till", "plant", "water", "harvest")) for a in out):
        out.append(untilled_step(p) or "go to soil")
    if p.holding_can and (p.can_charge or 0) <= 2:
        out.append("go to source")
    if not p.holding_can and p.can_holder:
        out.append(f"go to {p.can_holder}, and say to ask {p.can_holder} for the can")
    out.append("wait")
    return "Useful actions now: " + " · ".join(out) + "."


def heard(p: Percept) -> list[str]:
    out = []
    for e in p.witnessed:
        match e["type"]:
            case "Said" if e["agent"] == p.me:
                out.append(f'you said: "{e["text"]}"')
            case "Said":
                out.append(f'{e["agent"]} said: "{e["text"]}"')
            case "Gave" if e["to"] == p.me:
                out.append(f'{e["agent"]} gave you {e["qty"]} {label(e["item"])}')
            case "Gave":
                out.append(f'you gave {e["to"]} {e["qty"]} {label(e["item"])}')
            case "Rejected":
                out.append(f'your {e["action"]} failed: {e["reason"]}')
            case "Examined":
                out.append(f'you examined ({e["x"]},{e["y"]}): {p.catalog["lore"][e["lore"]]["text"]}')
    return out


def render(p: Percept, features: frozenset[str] | None = None) -> str:
    """The percept as text. `features` (see llm.STAGES) leaves out what a stage did not have yet; None: everything."""
    # None (watch, scripted examples, tests): the drawn grid and every older feature; a staged brain
    # passes its own features, words (stage 6) and actions (stage 7) included when it has them.
    has = (lambda f: f not in ("words", "actions")) if features is None else (lambda f: f in features)
    o = p.objective
    lines = [f"day {p.day}, {p.hour % 24:02d}:00 · {p.world} ({p.plane}) · loop {p.loop}"]
    lines.append(f"You are {p.me} at ({p.x},{p.y}). Energy {p.energy}/{p.max_energy}.")
    # One name for one object: the rules and the actions say "can"; the world's name for it follows
    # in brackets (2026-10-06: "coolant flask" here, "can" there, left the link to the model).
    alias = "" if p.can_name in ("", "can") else f"{p.can_name}, "
    if p.holding_can:
        lines.append(f"You hold the can ({alias}{p.can_charge}/{p.can_size}).")
    elif p.can_holder is not None:
        lines.append(f"{p.can_holder} holds the can" + (f" ({alias[:-2]})." if alias else "."))
    inv = ", ".join(f"{label(i)} x{n}" for i, n in sorted(p.inventory.items())) or "nothing"
    lines.append(f"You carry: {inv}.")
    if has("words"):
        lines += space(p)
    else:
        lines.append("Around you (x across, y down):")
        lines += grid(p)
        tiles = p.catalog["tiles"]
        kinds = sorted({t.kind for t in p.tiles.values()})
        legend = [f"{k} {tiles[k]['name']}" for k in kinds]
        legend += ["= tilled", "* watered", "0-9 growing (days)", "! ripe", "@ you"]
        legend += [f"{o_[0].upper()} {o_}" for o_ in sorted(p.others)]
        lines.append("Legend: " + " · ".join(legend))
    lines.append(f"Next to you: {adjacent(p)}.")
    if has("reach"):
        lines += reach(p)
    crops = ", ".join(f"{c} from {v['seeds']}, {v['days']} watered days" for c, v in p.catalog["crops"].items())
    lines.append(f"Crops: {crops}.")
    recipes = p.catalog.get("recipes") or {}
    if recipes and has("recipes"):
        def items(d):
            return " + ".join(f"{n} {label(i)}" for i, n in d.items())
        lines.append("Recipes (craft): " + "; ".join(
            f"{name}: {items(r['needs'])} -> {items(r['makes'])}" for name, r in recipes.items()) + ".")
    if has("actions"):
        lines.append(affordances(p))
    h = heard(p)
    if h:
        lines.append("Since your last turn:")
        lines += [f"- {x}" for x in h]
    lines.append(
        f"Goal: harvest {o['count']} {label(o['harvest'])} by the end of day {o['by_day']} "
        f"(so far {p.harvested})."
    )
    return "\n".join(lines)


def observe(w: World, me: str, since: int | None = None) -> str:
    return render(perceive(w, me, since))

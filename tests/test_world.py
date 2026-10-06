import copy
import json
from pathlib import Path

import pytest

from hoshi7 import World, load
from hoshi7.events import Ended, EVENTS, Examined, Gathered, Harvested, Moved, Rejected, Said, Tilled, from_dict
from hoshi7.schema import render
from hoshi7.view import observe
from hoshi7.world import snapshot

ROOT = Path(__file__).resolve().parent.parent

TINY = {
    "name": "tiny",
    "plane": "test",
    "max_energy": 10,
    # x across, y down: a spawns at (1,0) beside the source, b below it.
    "map": "~.,,.?\n..,,#.\n......\n......\n",
    "tiles": {
        ".": {"name": "floor", "walk": True},
        ",": {"name": "bed", "walk": True, "soil": True},
        "~": {"name": "well", "source": True},
        "#": {"name": "scrap", "gather": {"yields": {"alloy": 2}, "energy": 4, "becomes": "."}},
        "?": {"name": "stone", "lore": "stone"},
    },
    "can": {"name": "can", "size": 3},
    "crops": {"moss": {"seeds": "spores", "days": 2}},
    "recipes": {"lamp": {"needs": {"alloy": 2}, "makes": {"lamp": 1}}},
    "lore": {"stone": {"text": "It remembers."}},
    "objective": {"harvest": "moss", "count": 2, "by_day": 5},
    "spawns": [
        {"at": [1, 0], "inventory": {"spores": 5}, "tools": ["can"]},
        {"at": [1, 1], "inventory": {"spores": 5}},
        {"at": [5, 3], "inventory": {}},
    ],
}


def world(*agents: str, spec: dict | None = None) -> World:
    w = World.create(copy.deepcopy(spec or TINY))
    for a in agents:
        w.join(a)
    return w


def next_day(w: World) -> None:
    day = w.state.day
    while w.state.day == day and w.state.outcome is None:
        w.advance()


def only(events, cls):
    assert len(events) >= 1 and isinstance(events[0], cls), events
    return events[0]


@pytest.mark.parametrize("name", ["rooftop", "conservatory", "station"])
def test_world_files_load_and_render(name):
    w = World.create(load(ROOT / "worlds" / f"{name}.yaml"))
    for a in ("ada", "hal", "marc"):
        w.join(a)
    text = observe(w, "ada")
    assert "@" in text and "Goal:" in text and w.state.plane in text


def test_farm_cycle_till_plant_water_grow_harvest():
    w = world("ada")
    only(w.act("ada", {"type": "till", "dir": "e"}), type(w.log[-1]))
    w.advance()
    only(w.act("ada", {"type": "plant", "dir": "e", "crop": "moss"}), type(w.log[-1]))
    w.advance()
    w.act("ada", {"type": "water", "dir": "e"})
    assert w.state.can_charge == 2
    next_day(w)
    assert w.state.tile(2, 0).grown == 1 and not w.state.tile(2, 0).watered
    r = only(w.act("ada", {"type": "harvest", "dir": "e"}), Rejected)
    assert "not ripe" in r.reason
    w.act("ada", {"type": "water", "dir": "e"})
    next_day(w)
    only(w.act("ada", {"type": "harvest", "dir": "e"}), Harvested)
    assert w.state.agents["ada"].inventory["moss"] == 1
    assert w.state.agents["ada"].inventory["spores"] == 4
    assert w.state.harvested == {"moss": 1}


def test_unwatered_crop_does_not_grow():
    w = world("ada")
    w.act("ada", {"type": "till", "dir": "e"})
    w.advance()
    w.act("ada", {"type": "plant", "dir": "e", "crop": "moss"})
    next_day(w)
    assert w.state.tile(2, 0).grown == 0


def test_one_action_per_hour_and_one_word():
    w = world("ada", "hal")
    w.act("ada", {"type": "wait"})
    r = only(w.act("ada", {"type": "till", "dir": "e"}), Rejected)
    assert r.reason == "already acted this hour"
    only(w.act("ada", {"type": "say", "text": "morning"}), Said)
    only(w.act("ada", {"type": "say", "text": "again"}), Rejected)
    w.advance()
    only(w.act("ada", {"type": "say", "text": "new hour"}), Said)


def test_the_can_is_shared_by_giving_it():
    w = world("ada", "hal")
    w.act("hal", {"type": "till", "dir": "e"})
    w.advance()
    r = only(w.act("hal", {"type": "water", "dir": "e"}), Rejected)
    assert r.reason == "not holding the can: ada holds it, and only the holder can give it"
    w.act("ada", {"type": "give", "to": "hal", "item": "can"})
    assert w.state.can_holder == "hal"
    w.act("hal", {"type": "water", "dir": "e"})
    assert w.state.tile(2, 1).watered


def test_refill_needs_the_can_and_a_source_within_reach():
    w = world("ada", "hal")
    w.act("ada", {"type": "till", "dir": "e"})
    w.advance()
    w.act("ada", {"type": "water", "dir": "e"})
    w.advance()
    w.act("ada", {"type": "refill"})
    assert w.state.can_charge == 3
    w.advance()
    w.act("ada", {"type": "give", "to": "hal", "item": "can"})
    w.advance()
    r = only(w.act("hal", {"type": "refill"}), Rejected)
    assert r.reason == "no source within reach"


def test_move_reaches_five_steps_around_obstacles_only():
    w = world("ada", "hal")
    w.act("ada", {"type": "move", "x": 4, "y": 2})
    assert (w.state.agents["ada"].x, w.state.agents["ada"].y) == (4, 2)
    for goal, reason in [((0, 0), "cannot stand there"), ((1, 1), "cannot stand there"), ((4, 2), "already there")]:
        w.advance()
        r = only(w.act("ada", {"type": "move", "x": goal[0], "y": goal[1]}), Rejected)
        assert r.reason == reason
    w2 = world("ada")
    r = only(w2.act("ada", {"type": "move", "x": 5, "y": 3}), Rejected)
    assert r.reason.startswith("no path within")


def test_gather_costs_energy_and_changes_the_ground():
    w = world("ada")
    w.act("ada", {"type": "move", "x": 4, "y": 0})
    w.advance()
    g = only(w.act("ada", {"type": "gather", "dir": "s"}), Gathered)
    assert g.yields == {"alloy": 2}
    assert w.state.agents["ada"].energy == 6
    assert w.state.tile(4, 1).kind == "."
    w.advance()
    only(w.act("ada", {"type": "craft", "recipe": "lamp"}), type(w.log[-1]))
    assert w.state.agents["ada"].inventory.get("lamp") == 1 and "alloy" not in w.state.agents["ada"].inventory


def test_too_tired_to_gather():
    spec = copy.deepcopy(TINY)
    spec["tiles"]["#"]["gather"]["energy"] = 11
    w = world("ada", spec=spec)
    w.act("ada", {"type": "move", "x": 4, "y": 0})
    w.advance()
    r = only(w.act("ada", {"type": "gather", "dir": "s"}), Rejected)
    assert r.reason.startswith("too tired")


def test_examine_reveals_lore():
    w = world("ada")
    w.act("ada", {"type": "move", "x": 4, "y": 0})
    w.advance()
    e = only(w.act("ada", {"type": "examine", "dir": "e"}), Examined)
    assert w.state.lore[e.lore]["text"] == "It remembers."


def test_words_carry_six_tiles():
    w = world("ada", "hal", "marc")
    s = only(w.act("ada", {"type": "say", "text": "the well is to the west"}), Said)
    assert s.hearers == ["hal"]


def test_give_needs_reach_and_stock():
    w = world("ada", "hal", "marc")
    assert "out of reach" in only(w.act("ada", {"type": "give", "to": "marc", "item": "spores"}), Rejected).reason
    assert "not enough" in only(w.act("ada", {"type": "give", "to": "hal", "item": "spores", "qty": 9}), Rejected).reason
    w.act("ada", {"type": "give", "to": "hal", "item": "spores", "qty": 2})
    assert w.state.agents["hal"].inventory["spores"] == 7


def test_a_new_day_restores_energy_and_turns():
    w = world("ada")
    w.act("ada", {"type": "till", "dir": "e"})
    assert w.state.agents["ada"].energy == 8
    next_day(w)
    a = w.state.agents["ada"]
    assert (w.state.day, w.state.hour, a.energy, a.acted) == (2, 6, 10, False)


def test_the_world_is_won_by_the_goal_and_lost_by_the_calendar():
    spec = copy.deepcopy(TINY)
    spec["objective"]["count"] = 1
    w = world("ada", spec=spec)
    w.act("ada", {"type": "till", "dir": "e"})
    w.advance()
    w.act("ada", {"type": "plant", "dir": "e", "crop": "moss"})
    for _ in range(2):
        w.advance()
        w.act("ada", {"type": "water", "dir": "e"})
        next_day(w)
    out = w.act("ada", {"type": "harvest", "dir": "e"})
    assert isinstance(out[-1], Ended) and out[-1].outcome == "won"
    assert only(w.act("ada", {"type": "wait"}), Rejected).reason.startswith("the world has ended")

    lost = world("ada")
    while lost.state.outcome is None:
        lost.advance()
    assert lost.state.outcome == "lost" and lost.state.day == 6


def test_malformed_and_unknown_actions_are_refused_not_raised():
    w = world("ada")
    assert "malformed" in only(w.act("ada", {"type": "move"}), Rejected).reason
    assert "unknown action" in only(w.act("ada", {"type": "fly"}), Rejected).reason
    assert only(w.act("ghost", {"type": "wait"}), Rejected).reason == "not in this world"


def test_the_log_replays_into_the_same_world_through_json():
    w = world("ada", "hal")
    w.act("ada", {"type": "till", "dir": "e"})
    w.act("hal", {"type": "say", "text": "I will gather"})
    w.advance()
    w.act("ada", {"type": "plant", "dir": "e", "crop": "moss"})
    w.act("hal", {"type": "move", "x": 3, "y": 2})
    next_day(w)
    w.act("ada", {"type": "give", "to": "hal", "item": "can"})
    wire = json.loads(json.dumps([e.to_dict() for e in w.log]))
    again = World.replay([from_dict(d) for d in wire])
    assert snapshot(again.state) == snapshot(w.state)


def test_view_tells_what_was_heard_and_refused():
    w = world("ada", "hal")
    since = w.state.tick
    w.act("hal", {"type": "say", "text": "take the can to the beds"})
    w.act("ada", {"type": "fly"})
    text = observe(w, "ada", since=since)
    assert 'hal said: "take the can to the beds"' in text
    assert "your fly failed" in text
    assert "You hold the can (3/3)." in text


def test_schema_file_matches_the_events():
    assert (ROOT / "schemas" / "events.json").read_text() == render()
    schema = json.loads(render())
    assert set(schema["$defs"]) == set(EVENTS)


def test_a_give_finds_its_receiver_whatever_the_case():
    from hoshi7 import World, load
    from pathlib import Path
    w = World.create(load(Path(__file__).resolve().parent.parent / "worlds" / "rooftop.yaml"))
    w.join("ada")
    w.join("ben")
    ax, ay = w.state.agents["ada"].x, w.state.agents["ada"].y
    w.act("ben", {"type": "move", "x": ax + 1, "y": ay})
    if (w.state.agents["ben"].x, w.state.agents["ben"].y) != (ax + 1, ay):
        w.act("ben", {"type": "move", "x": ax, "y": ay + 1})
    w.act("ada", {"type": "give", "to": "Ben", "item": "can"})
    assert w.state.can_holder == "ben"


def test_go_walks_toward_a_named_place_and_stops_next_to_it():
    from hoshi7 import World, load
    from pathlib import Path
    w = World.create(load(Path(__file__).resolve().parent.parent / "worlds" / "rooftop.yaml"))
    w.join("ada")
    w.join("ben")

    def go(to):
        ev = w.act("ada", {"type": "go", "to": to})
        w.advance()
        return [type(e).__name__ for e in ev]

    for _ in range(6):  # one go per hour, until next to the cistern
        if "Rejected" in go("Source"):
            break
    a = w.state.agents["ada"]
    assert any(w.state.inside(a.x + dx, a.y + dy) and w.state.spec(a.x + dx, a.y + dy).get("source")
               for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0)))
    assert go("ben") == ["Moved"]
    assert go("nowhere") == ["Rejected"]


def test_a_missing_parameter_is_named_in_the_refusal():
    w = world("a")
    w.act("a", {"type": "till", "dir": "e"})
    w.advance()
    r = only(w.act("a", {"type": "plant", "dir": "e"}), Rejected)
    assert r.reason == "malformed action: plant needs 'crop'"


def test_an_aimed_action_without_its_tile_is_refused_not_played_here():
    w = world("a")
    assert only(w.act("a", {"type": "till"}), Rejected).reason == "which tile? (x and y, or dir)"
    assert only(w.act("a", {"type": "till", "x": 2}), Rejected).reason == "give both x and y of the tile"
    assert only(w.act("a", {"type": "till", "x": 2, "y": 0}), Tilled)


def test_go_to_the_tile_one_stands_on_is_refused_not_a_step_away():
    w = world("a")
    a = w.state.agents["a"]
    assert only(w.act("a", {"type": "go", "x": a.x, "y": a.y}), Rejected).reason == f"already at ({a.x},{a.y})"


def test_the_can_refusal_names_the_holder_only_within_sight():
    w = world("ada", "hal", "cyd")             # cyd spawns at (5,3), within sight of ada at (1,0)
    w.emit(Moved(0, "ada", 5, 0))
    w.emit(Moved(0, "cyd", 0, 3))
    w.advance()
    r = only(w.act("cyd", {"type": "water", "dir": "e"}), Rejected)
    assert r.reason == "not holding the can: ada holds it, and only the holder can give it"
    big = copy.deepcopy(TINY)
    big["map"] = "~" + "." * 11 + "\n" + "." * 12 + "\n"
    big["spawns"] = [{"at": [1, 0], "inventory": {}, "tools": ["can"]}, {"at": [11, 1], "inventory": {}}]
    w = world("ada", "hal", spec=big)
    r = only(w.act("hal", {"type": "refill"}), Rejected)
    assert r.reason == "not holding the can: someone out of sight holds it, and only the holder can give it"

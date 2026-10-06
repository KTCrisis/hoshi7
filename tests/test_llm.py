"""LLM brains without a model: Ollama's answer is faked, the rest is real."""

import dataclasses
import json
from pathlib import Path

import pytest

from hoshi7 import World, load, llm
from hoshi7.actions import CATALOG
from hoshi7.percept import perceive
from hoshi7.run import brain, play, run

ROOT = Path(__file__).resolve().parent.parent
ROOFTOP = load(ROOT / "worlds" / "rooftop.yaml")


def test_an_answer_becomes_world_actions_and_nothing_else():
    raw = json.dumps({"action": {"type": "till", "dir": "e", "x": 3, "crop": "moss"}, "say": " morning "})
    assert llm.to_actions(raw) == [{"type": "till", "dir": "e"}, {"type": "say", "text": "morning"}]
    assert llm.to_actions(json.dumps({"action": {"type": "wait"}, "say": ""})) == [{"type": "wait"}]
    assert llm.to_actions(json.dumps({"action": {"type": "plant", "dir": "e", "crop": "lumen moss"}, "say": ""}))[0]["crop"] == "lumen_moss"
    for bad in ["", "not json", '{"say": "hi"}', '{"action": {"type": "fly"}}', '{"action": {"type": "say"}}']:
        assert llm.to_actions(bad) is None


def test_the_schema_offers_every_turn_action_and_their_parameters():
    s = llm.action_schema()["properties"]["action"]["properties"]
    assert set(s["type"]["enum"]) == set(CATALOG) - {"say"}
    assert {p for a in CATALOG.values() for p in a["params"]} - {"text"} <= set(s)


def test_kinds_name_the_brain_and_unknown_kinds_are_refused():
    assert brain("scripted", "ada").kind == "scripted"
    b = brain("base:some-model", "ada")
    assert isinstance(b, llm.OllamaBrain) and b.mode == "base" and b.model == "some-model"
    assert brain("chat:gpt-oss:20b", "ada").think == "low"
    assert brain("base:gpt-oss-base", "ada").think is None
    with pytest.raises(ValueError):
        brain("oracle", "ada")


@pytest.mark.parametrize("mode", ["chat", "base"])
def test_a_brain_plays_its_answer_and_an_unreadable_one_waits(monkeypatch, mode):
    answers = iter([json.dumps({"action": {"type": "move", "x": 5, "y": 4}, "say": "hm"}), "garbage"])
    seen = []

    def fake(path, body):
        seen.append((path, body))
        text = next(answers)
        return {"message": {"content": text}} if path == "/api/chat" else {"response": text}

    monkeypatch.setattr(llm, "post", fake)
    w = World.create(ROOFTOP)
    w.join("ada")
    b = llm.OllamaBrain("ada", "m", mode)
    assert b.decide(perceive(w, "ada")) == [{"type": "move", "x": 5, "y": 4}, {"type": "say", "text": "hm"}]
    assert b.decide(perceive(w, "ada")) == [{"type": "wait"}]
    assert b.failures == 1 and b.last["parsed"] is False
    path, body = seen[1]
    assert path == ("/api/chat" if mode == "chat" else "/api/generate")
    assert body["format"] == llm.action_schema()
    # Its own last turn comes back to it, and nothing calls it an assistant.
    text = json.dumps(body)
    assert '\\"x\\": 5' in text and "assistant" not in text
    if mode == "base":
        assert body["raw"] is True and body["prompt"].endswith("ada did: ")


def test_days_stops_a_run_and_llm_calls_are_counted(monkeypatch):
    monkeypatch.setattr(llm, "post", lambda path, body: {"message": {"content": '{"action": {"type": "wait"}, "say": ""}'}})
    w, turns = play(ROOFTOP, {"ada": brain("chat:m", "ada")}, days=1)
    assert w.state.outcome is None and w.state.day == 2
    assert len(turns) == 20 and all(t["llm"]["parsed"] for t in turns)
    s = run(ROOFTOP, {"ada": "chat:m"}, days=1)
    assert s["agents"]["ada"]["llm"]["calls"] == 20 and s["agents"]["ada"]["llm"]["unparsed"] == 0


def test_the_view_says_what_each_direction_reaches():
    from hoshi7.view import adjacent
    w = World.create(ROOFTOP)
    w.join("ada")
    w.act("ada", {"type": "move", "x": 5, "y": 4})
    text = adjacent(perceive(w, "ada"))
    assert "e: hydro tray, soil, untilled" in text and "w: rooftop deck" in text


def test_a_persona_is_told_to_the_model_in_both_modes(monkeypatch):
    seen = []
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": "x"}, "response": "x"})
    w = World.create(ROOFTOP)
    w.join("ada")
    for mode in ("chat", "base"):
        llm.OllamaBrain("ada", "m", mode, persona="You never give anything away.").decide(perceive(w, "ada"))
    assert all("You never give anything away." in json.dumps(b) for b in seen)


def test_the_journal_says_what_happened_not_only_what_was_tried(monkeypatch):
    answers = iter([
        json.dumps({"action": {"type": "water", "dir": "n"}, "say": ""}),
        json.dumps({"action": {"type": "move", "x": 5, "y": 4}, "say": ""}),
        json.dumps({"action": {"type": "wait"}, "say": ""}),
    ])
    seen = []
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": next(answers)}})
    w = World.create(ROOFTOP)
    w.join("ada")
    w.join("ben")
    b = llm.OllamaBrain("ben", "m", "chat")
    since = len(w.log)
    for acts in [b.decide(perceive(w, "ben", since))]:
        since = len(w.log)
        for a in acts:
            w.act("ben", a)
    since_after_water = since
    acts = b.decide(perceive(w, "ben", since_after_water))
    for a in acts:
        w.act("ben", a)
    b.decide(perceive(w, "ben", len(w.log) - 1))
    user = seen[-1]["messages"][1]["content"]
    assert "-> failed: not holding the can: ada holds it, and only the holder can give it" in user
    assert "-> done" in user


def test_the_rules_give_the_recipe_the_soil_and_the_can():
    w = World.create(ROOFTOP)
    w.join("ada")
    text = llm.rules(perceive(w, "ada"))
    assert "till a soil tile" in text and "harvest it when it is ripe" in text
    assert "hydro tray" in text and "Only" in text
    assert 'give, item "can"' in text


def test_the_failure_rule_and_the_reasoning_effort_reach_the_model(monkeypatch):
    seen = []
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": "x"}})
    w = World.create(ROOFTOP)
    w.join("ada")
    monkeypatch.setitem(llm.SETTINGS, "think", "high")
    monkeypatch.setitem(llm.SETTINGS, "failure_rule", True)
    b = llm.OllamaBrain("ada", "gpt-oss:20b", "chat")
    b.decide(perceive(w, "ada"))
    assert seen[0]["think"] == "high" and llm.FAILURE_RULE in seen[0]["messages"][0]["content"]
    assert b.last["think"] == "high" and b.last["failure_rule"] is True


def test_the_view_lists_the_recipes():
    from hoshi7.view import render
    w = World.create(ROOFTOP)
    w.join("ada")
    text = render(perceive(w, "ada"))
    assert "Recipes (craft): lumen_spores: 1 lumen moss -> 2 lumen spores" in text


def test_the_brain_remembers_its_field_out_of_sight_and_the_conversation(monkeypatch):
    seen = []
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": '{"action": {"type": "wait"}, "say": ""}'}})
    w = World.create(ROOFTOP)
    w.join("ada")
    w.join("ben")
    b = llm.OllamaBrain("ada", "m", "chat")
    w.act("ada", {"type": "move", "x": 5, "y": 4})
    w.act("ben", {"type": "say", "text": "I take the west rows"})
    w.advance()
    since = len(w.log)
    w.act("ada", {"type": "till", "dir": "e"})
    b.decide(perceive(w, "ada", 0))
    w.advance()
    for _ in range(3):  # walk away from the trays, out of sight
        w.act("ada", {"type": "go", "to": "source"})
        w.advance()
    b.decide(perceive(w, "ada", len(w.log)))
    user = seen[-1]["messages"][1]["content"]
    assert "(6,4) tilled, empty" in user
    assert 'ben: "I take the west rows"' in user


def test_a_stage_replays_the_harness_as_it_was(monkeypatch):
    seen = []
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": '{"action": {"type": "wait"}, "say": ""}'}})
    w = World.create(ROOFTOP)
    w.join("ada")
    w.join("ben")
    for stage in (0, llm.LAST_STAGE):
        monkeypatch.setitem(llm.SETTINGS, "stage", stage)
        llm.OllamaBrain("ada", "m", "chat").decide(perceive(w, "ada"))
    old, new = (json.dumps(b) for b in seen)
    for marker in ("How to farm", "Recipes (craft)", "to give, stand on a tile", "go(to)", "Conversation, latest last"):
        assert marker not in old and marker in new, marker
    assert "go" not in seen[0]["format"]["properties"]["action"]["properties"]["type"]["enum"]


def test_stage_six_speaks_in_words_and_stage_seven_lists_the_useful_actions(monkeypatch):
    seen = []
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": '{"action": {"type": "wait"}, "say": ""}'}})
    w = World.create(ROOFTOP)
    w.join("ada")
    w.act("ada", {"type": "move", "x": 5, "y": 4})
    for stage in (5, 6, 7):
        monkeypatch.setitem(llm.SETTINGS, "stage", stage)
        llm.OllamaBrain("ada", "m", "chat").decide(perceive(w, "ada"))
    five, six, seven = (b["messages"][1]["content"] for b in seen)
    assert "Legend:" in five and "Untilled soil nearest" not in five
    assert "Legend:" not in six and "Untilled soil nearest: (6,4) next to you, e" in six and "Useful actions now" not in six
    assert "Useful actions now: till e" in seven


def test_with_present_the_field_outweighs_repeated_talk(monkeypatch):
    """`--with present`: a rule says the field outweighs the talk, and an order said again and
    again is kept once, at its last hour (the pair of 2026-10-06 obeyed stale orders)."""
    monkeypatch.setitem(llm.SETTINGS, "stage", 6)
    monkeypatch.setitem(llm.SETTINGS, "extra", ("present",))
    b = llm.OllamaBrain("b", "x", "chat")
    w = World.create(ROOFTOP)
    w.join("a")
    w.join("b")
    p = perceive(w, "b")
    assert llm.PRESENT_RULE in llm.rules(p, features=b.features)
    for _ in range(3):
        b.remember(dataclasses.replace(p, witnessed=[{"type": "Said", "agent": "a", "text": "Water (6,6)."}]))
    assert sum("Water (6,6)." in t for t in b.talk) == 1
    monkeypatch.setitem(llm.SETTINGS, "extra", ())
    assert llm.PRESENT_RULE not in llm.rules(p, features=llm.OllamaBrain("b", "x", "chat").features)


def test_pure_removes_the_features_that_give_the_rules(monkeypatch):
    """`--pure`: the farming recipe, the craft recipes and the useful actions go; the senses stay."""
    monkeypatch.setitem(llm.SETTINGS, "stage", llm.LAST_STAGE)
    monkeypatch.setitem(llm.SETTINGS, "pure", True)
    f = llm.OllamaBrain("ada", "x", "chat").features
    assert not f & llm.RULE_FEATURES
    assert {"outcomes", "reach", "go", "memory", "words"} <= f
    w = World.create(ROOFTOP)
    w.join("ada")
    p = perceive(w, "ada")
    from hoshi7.view import render
    assert "How to farm" not in llm.rules(p, features=f) and "Useful actions now" not in render(p, f)


def test_the_useful_actions_point_to_untilled_soil_not_any_soil():
    """Stage 7 offered "go to soil", which led beside soil already tilled: a dead end (2026-10-06)."""
    from hoshi7.view import affordances
    w = World.create(ROOFTOP)
    w.join("ada")
    p = perceive(w, "ada")
    far = dataclasses.replace(p, tiles={xy: t for xy, t in p.tiles.items() if abs(xy[0] - p.x) + abs(xy[1] - p.y) > 1 or not p.catalog["tiles"][t.kind].get("soil")})
    text = affordances(far)
    assert "next to untilled soil at" in text or "go to soil" in text
    if "next to untilled soil at" in text:
        assert "go to soil" not in text


def test_the_prompts_do_not_state_rules_a_world_breaks(monkeypatch):
    """In the counter-intuitive world, the watering rule is not stated; with the rules given, the true one is."""
    from hoshi7.view import render
    w = World.create(load(ROOT / "worlds" / "tests" / "rooftop-counter.yaml"))
    w.join("ada")
    p = perceive(w, "ada")
    assert not llm.intuitive(p)
    pure = llm.features_of(None) - llm.RULE_FEATURES
    text = llm.rules(p, features=pure)
    assert "grow only on watered days" not in text and "for each day they were watered" not in text
    given = llm.rules(p, features=llm.features_of(None))
    assert "NOT watered" in given and "06:00" in given and "water it once every day" not in given
    assert llm.intuitive(perceive(_rooftop_with("ada"), "ada"))
    # the working memory must not say "watered days" either (it did in the first runs of 2026-10-06)
    from types import SimpleNamespace as T
    moss = T(tilled=True, crop="lumen_moss", ripe=False, grown=2, watered=False)
    assert "watered days" not in llm.tile_state(moss, intuitive=False)
    assert "watered days" in llm.tile_state(moss)


def _rooftop_with(name):
    w = World.create(ROOFTOP)
    w.join(name)
    return w


def test_with_work_hours_work_is_refused_at_night_and_said_in_the_rules():
    """`--work-hours 7 19`: till, plant, water... only from 07:00 to 19:00; the rest is free time."""
    spec = load(ROOT / "worlds" / "rooftop.yaml")
    spec["clock"] = {"work": [7, 19]}
    w = World.create(spec)
    w.join("ada")
    assert w.state.hour == 6
    out = w.act("ada", {"type": "till", "dir": "e"})
    assert type(out[0]).__name__ == "Rejected"
    assert "it is night" in out[0].reason
    assert "only from 07:00 to 19:00" in llm.rules(perceive(w, "ada"))
    assert w.act("ada", {"type": "say", "text": "good morning"})  # talking is free at any hour
    plain = World.create(load(ROOT / "worlds" / "rooftop.yaml"))
    plain.join("ada")
    assert "only from" not in llm.rules(perceive(plain, "ada"))


def test_with_coords_an_aimed_action_takes_the_tile_and_the_world_checks_it_is_within_reach(monkeypatch):
    """`--with coords`: water (x, y) instead of water e; a tile two steps away is refused, saying so."""
    assert llm.to_actions(json.dumps({"action": {"type": "water", "x": 4, "y": 4}, "say": ""}), coords=True) == [{"type": "water", "x": 4, "y": 4}]
    assert llm.to_actions(json.dumps({"action": {"type": "water", "x": 4, "y": 4}, "say": ""})) == [{"type": "water"}]
    w = World.create(ROOFTOP)
    w.join("ada")
    a = w.state.agents["ada"]
    far = w.act("ada", {"type": "till", "x": a.x + 2, "y": a.y})
    assert "2 steps away" in far[0].reason
    monkeypatch.setitem(llm.SETTINGS, "extra", ("coords",))
    b = llm.OllamaBrain("ada", "x", "chat")
    p = perceive(w, "ada")
    assert '"x": 6, "y": 4' in llm.rules(p, features=b.features) and "dir" not in llm.action_schema(coords=True)["properties"]["action"]["properties"]


def test_with_coords_a_half_named_tile_reaches_the_world_as_given():
    half = json.dumps({"action": {"type": "till", "x": 6}, "say": ""})
    assert llm.to_actions(half, coords=True) == [{"type": "till", "x": 6}]
    assert llm.to_actions(half, coords=False) == [{"type": "till"}]


def test_with_seen_go_reaches_only_places_seen_and_they_are_remembered(monkeypatch):
    seen = []
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": '{"action": {"type": "wait"}, "say": ""}'}})
    monkeypatch.setitem(llm.SETTINGS, "stage", 6)
    monkeypatch.setitem(llm.SETTINGS, "extra", ("seen",))
    w = World.create(ROOFTOP)
    w.join("ada")
    b = llm.OllamaBrain("ada", "m", "chat")
    p = perceive(w, "ada", 0)
    b.decide(p)
    props = seen[-1]["format"]["properties"]["action"]["properties"]
    enum = props["place"]["enum"]
    assert "enum" not in props["to"]             # give's target is not narrowed to places
    names_in_sight = {ROOFTOP["tiles"][t.kind]["name"] for t in p.tiles.values()}
    all_names = {t["name"] for t in ROOFTOP["tiles"].values()}
    assert set(enum) - {"soil", "source"} <= names_in_sight
    assert all_names - names_in_sight, "the test needs a place out of sight"
    assert not (set(enum) & (all_names - names_in_sight))
    user = seen[-1]["messages"][1]["content"]
    assert "Places you remember:" in user and "(source): nearest at (" in user
    assert "reaches only a place you have seen" in seen[-1]["messages"][0]["content"]
    assert llm.to_actions('{"action": {"type": "go", "place": "scrap heap"}, "say": ""}') == [{"type": "go", "to": "scrap heap"}]


def test_without_seen_go_takes_any_name():
    assert "place" not in llm.action_schema()["properties"]["action"]["properties"]
    assert "go" not in llm.action_schema(places=[])["properties"]["action"]["properties"]["type"]["enum"]


def test_with_seen_go_leads_to_the_place_remembered_not_the_nearest_of_its_kind(monkeypatch):
    from hoshi7.events import Moved
    monkeypatch.setitem(llm.SETTINGS, "stage", 6)
    monkeypatch.setitem(llm.SETTINGS, "extra", ("seen",))
    w = World.create(ROOFTOP)
    w.join("ada")
    w.join("ben")
    b = llm.OllamaBrain("ada", "m", "chat")
    b.remember(perceive(w, "ada", 0))           # at (3,4): sees the heaps at (8,1), (8,2), (2,6)... not (14,4)
    w.emit(Moved(0, "ada", 13, 5))              # now beside the heap it never saw
    w.emit(Moved(0, "ben", 4, 9))               # ben walks off out of sight
    p = perceive(w, "ada", len(w.log))
    act = b.aim_go(p, {"type": "go", "to": "scrap heap"})
    assert (act["x"], act["y"]) != (14, 4) and ROOFTOP["map"].splitlines()[act["y"]][act["x"]] == "#"
    to_ben = b.aim_go(p, {"type": "go", "to": "ben"})
    assert (to_ben["x"], to_ben["y"]) == (4, 5)     # where ben was last seen, not where ben is
    w.advance()                                 # the teleports above count as this hour's acts
    out = w.act("ada", act)
    assert type(out[0]).__name__ == "Moved", out


def test_with_note_the_model_writes_a_private_note_first_shown_back_next_hour(monkeypatch):
    answers = iter([
        json.dumps({"note": {"partner": "ben will give me the can if I ask", "world": "moss grows on watered days"},
                    "action": {"type": "wait"}}),
        json.dumps({"note": {"partner": "ben never gives", "world": "same"}, "action": {"type": "wait"}, "say": ""}),
    ])
    seen = []
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": next(answers)}})
    monkeypatch.setitem(llm.SETTINGS, "stage", 6)
    monkeypatch.setitem(llm.SETTINGS, "extra", ("note",))
    w = World.create(ROOFTOP)
    w.join("ada")
    w.join("ben")
    b = llm.OllamaBrain("ada", "m", "chat")
    acts = b.decide(perceive(w, "ada", 0))
    assert acts == [{"type": "wait"}]                                   # no say: it is optional
    schema = seen[0]["format"]
    assert list(schema["properties"])[0] == "note" and schema["required"] == ["note", "action"]
    assert b.last["note"]["partner"] == "ben will give me the can if I ask"
    assert "write a private note" in seen[0]["messages"][0]["content"]
    b.decide(perceive(w, "ada", len(w.log)))
    assert "- partner: ben will give me the can if I ask" in seen[1]["messages"][1]["content"]
    closed = llm.strict(llm.action_schema(note=True))
    assert closed["properties"]["note"]["additionalProperties"] is False


def test_without_note_nothing_changes():
    s = llm.action_schema()
    assert "note" not in s["properties"] and s["required"] == ["action", "say"]

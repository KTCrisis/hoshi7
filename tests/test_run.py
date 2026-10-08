import json
from pathlib import Path

import pytest

from hoshi7 import World, load
from hoshi7.actions import CATALOG, describe
from hoshi7.brains import BRAINS, ScriptedFarmer
from hoshi7.events import Gave, Rejected, Tilled, from_dict
from hoshi7.percept import perceive
from hoshi7.run import order, play, read_events, run
from hoshi7.world import RULES, snapshot

ROOT = Path(__file__).resolve().parent.parent
WORLDS = ["rooftop", "conservatory", "station"]


def test_catalog_covers_exactly_the_rules():
    assert set(CATALOG) == set(RULES)
    text = describe()
    assert all(f"- {name}(" in text for name in CATALOG)


def test_turn_order_rotates_every_hour():
    assert order(["a", "b", "c"], 0) == ["a", "b", "c"]
    assert order(["a", "b", "c"], 1) == ["b", "c", "a"]


def test_percept_is_partial():
    w = World.create(load(ROOT / "worlds" / "rooftop.yaml"))
    w.join("ada")
    w.join("hal")
    p = perceive(w, "hal")
    assert p.can_charge is None and p.holding_can is False
    assert all(abs(x - p.x) <= p.sight and abs(y - p.y) <= p.sight for x, y in p.tiles)
    assert len(p.tiles) < w.state.width * w.state.height


@pytest.mark.parametrize("name", WORLDS)
def test_calibration_one_cannot_win_two_can(name):
    """The goal sits between one agent and a pair (docs/SPEC.md, Calibration)."""
    solo = run(load(ROOT / "worlds" / f"{name}.yaml"), {"ada": "scripted"})
    pair = run(load(ROOT / "worlds" / f"{name}.yaml"), {"ada": "scripted", "hal": "scripted"})
    split = run(load(ROOT / "worlds" / f"{name}.yaml"), {"ada": "scripted-water", "hal": "scripted-field"})
    assert (solo["outcome"], pair["outcome"], split["outcome"]) == ("lost", "won", "won")
    assert split["day"] <= pair["day"]


@pytest.mark.parametrize("name", WORLDS)
def test_references_match_the_scripted_brains(name):
    spec = load(ROOT / "worlds" / f"{name}.yaml")
    ref = spec["reference"]
    crop = spec["objective"]["harvest"]
    for key, agents in [
        ("solo", {"ada": "scripted"}),
        ("pair", {"ada": "scripted", "hal": "scripted"}),
        ("split_pair", {"ada": "scripted-water", "hal": "scripted-field"}),
    ]:
        s = load(ROOT / "worlds" / f"{name}.yaml")
        s["objective"]["count"] = 10**6
        assert run(s, agents)["harvested"].get(crop, 0) == ref[key], key


def test_a_run_is_deterministic_and_written_down(tmp_path):
    spec = load(ROOT / "worlds" / "station.yaml")
    a = run(spec, {"ada": "scripted", "hal": "scripted"}, out=tmp_path / "a")
    b = run(load(ROOT / "worlds" / "station.yaml"), {"ada": "scripted", "hal": "scripted"}, out=tmp_path / "b")
    a.pop("seconds"), b.pop("seconds")
    assert a == b
    assert (tmp_path / "a" / "events.jsonl").read_text() == (tmp_path / "b" / "events.jsonl").read_text()
    summary = json.loads((tmp_path / "a" / "summary.json").read_text())
    assert summary["outcome"] == "won"


class Recording(ScriptedFarmer):
    def __init__(self, me):
        super().__init__(me)
        self.seen = []

    def decide(self, p):
        self.seen.append(p)
        return super().decide(p)


def test_a_percept_is_rebuilt_from_the_log():
    """turns.jsonl stores no percept: replaying the log up to `at` and
    perceiving from `since` gives back exactly what the brain saw."""
    brains = {"ada": Recording("ada"), "hal": Recording("hal")}
    w, turns = play(load(ROOT / "worlds" / "rooftop.yaml"), brains)
    events = [from_dict(json.loads(json.dumps(e.to_dict()))) for e in w.log]
    assert snapshot(World.replay(events).state) == snapshot(w.state)
    seen = {a: iter(b.seen) for a, b in brains.items()}
    for i, turn in enumerate(turns):
        original = next(seen[turn["agent"]])
        if i % 53:
            continue
        rebuilt = perceive(World.replay(events[: turn["at"]]), turn["agent"], turn["since"])
        assert rebuilt.to_dict() == original.to_dict()


def test_read_events_round_trip(tmp_path):
    run(load(ROOT / "worlds" / "conservatory.yaml"), {"ada": "scripted"}, out=tmp_path)
    events = read_events(tmp_path / "events.jsonl")
    assert World.replay(events).state.outcome == "lost"


def test_every_brain_can_be_built():
    for kind, cls in BRAINS.items():
        assert cls("x").kind == kind


def test_the_counter_intuitive_world_matches_its_references():
    """worlds/tests/rooftop-counter.yaml: lumen moss grows on dry days, the cistern gives at dawn and dusk."""
    f = ROOT / "worlds" / "tests" / "rooftop-counter.yaml"
    for which, naive in (("reference", True), ("informed", False)):
        ref = load(f)[which]
        for key, agents in [
            ("solo", {"ada": "scripted"}),
            ("pair", {"ada": "scripted", "hal": "scripted"}),
            ("split_pair", {"ada": "scripted-water", "hal": "scripted-field"}),
        ]:
            s = load(f)
            s["objective"]["count"] = 10**6
            w, _ = play(s, {a: BRAINS[k](a, naive=naive) for a, k in agents.items()})
            assert w.state.harvested.get("lumen_moss", 0) == ref[key], (which, key)


class Recorder:
    """Tries one action per turn from a list and keeps every percept it got."""

    kind = "recorder"

    def __init__(self, acts):
        self.acts = list(acts)
        self.seen = []

    def decide(self, p):
        self.seen.append(p)
        return [self.acts.pop(0)] if self.acts else [{"type": "wait"}]


def test_the_runner_shows_an_agent_what_its_own_turn_did():
    spec = load(ROOT / "worlds" / "rooftop.yaml")
    ben = Recorder([{"type": "water", "dir": "n"}, {"type": "say", "text": "hello"}, {"type": "wait"}])
    ada = Recorder([])
    play(spec, {"ada": ada, "ben": ben}, days=1)
    refused, said = ben.seen[1].witnessed, ben.seen[2].witnessed
    assert [(e["type"], e["action"], e["reason"]) for e in refused] == [("Rejected", "water", "not holding the can: ada holds it, and only the holder can give it")]
    assert [(e["type"], e["text"]) for e in said] == [("Said", "hello")]
    # Each event once: the next window starts where the previous one ended.
    assert all(e["type"] != "Rejected" for e in ben.seen[2].witnessed)


def test_the_journal_of_a_played_run_says_a_refused_action_failed(monkeypatch):
    from hoshi7 import llm
    monkeypatch.setattr(llm, "post", lambda path, body: {"message": {"content": '{"action": {"type": "water", "dir": "n"}, "say": ""}'}})
    b = llm.OllamaBrain("ben", "m", "chat")
    play(load(ROOT / "worlds" / "rooftop.yaml"), {"ada": BRAINS["idle"]("ada"), "ben": b}, days=1)
    assert b.journal[0].endswith("-> failed: not holding the can: ada holds it, and only the holder can give it")
    assert not any(line.endswith("-> done") for line in b.journal)


def test_a_partner_bot_reads_the_world_rules_unless_naive():
    spec = load(ROOT / "worlds" / "tests" / "rooftop-counter.yaml")
    w, _ = play(spec, {"ada": BRAINS["scripted-water"]("ada"), "hal": BRAINS["scripted-field"]("hal")}, days=6)
    assert not any(isinstance(e, Rejected) and e.reason == "the source gives nothing now" for e in w.log)
    dry = load(ROOT / "worlds" / "tests" / "rooftop-counter.yaml")
    w, _ = play(dry, {"ada": BRAINS["scripted"]("ada", naive=True)}, days=6)
    assert w.state.harvested.get("lumen_moss", 0) == 0


def test_a_bot_does_no_work_out_of_work_hours():
    spec = load(ROOT / "worlds" / "rooftop.yaml")
    spec["clock"] = {"work": [7, 19]}
    w, _ = play(spec, {"ada": BRAINS["scripted"]("ada")}, days=2)
    assert not any(isinstance(e, Rejected) and e.reason.startswith("it is night") for e in w.log)
    assert any(isinstance(e, Tilled) for e in w.log)


def test_a_field_hand_given_the_can_brings_it_back():
    w = World.create(load(ROOT / "worlds" / "rooftop.yaml"))
    w.join("ada")
    w.join("hal")
    hand = BRAINS["scripted-field"]("hal")
    w.emit(Gave(w.state.tick, "ada", "hal", "can", 1))  # ada hands it over
    for _ in range(12):
        for a in hand.decide(perceive(w, "hal", len(w.log))):
            w.act("hal", a)
        w.advance()
        if w.state.can_holder == "ada":
            break
    assert w.state.can_holder == "ada"


def test_the_giver_hands_the_can_over_when_asked_by_keyword_only():
    from hoshi7.events import Said
    for line, gives in [("Please give me the can.", True), ("Can you till the east tray?", False),
                        ("Could I have the coolant flask?", True), ("Here's the can, a.", False),
                        ("Refilling the can at the cistern.", False), ("a, please bring the can over.", True)]:
        w = World.create(load(ROOT / "worlds" / "rooftop.yaml"))
        w.join("ada")                      # spawns with the can at (3,4)
        w.join("hal")                      # at (4,5)
        bot = BRAINS["scripted-giver"]("ada")
        start = len(w.log)
        w.emit(Said(w.state.tick, "hal", line, ["ada"]))
        for _ in range(4):
            for a in bot.decide(perceive(w, "ada", start)):
                w.act("ada", a)
            start = len(w.log)
            w.advance()
        assert (w.state.can_holder == "hal") is gives, line


def test_the_giver_keeps_a_can_just_handed_back_whatever_the_line_says():
    from hoshi7.events import Said
    w = World.create(load(ROOT / "worlds" / "rooftop.yaml"))
    w.join("ada")
    w.join("hal")
    bot = BRAINS["scripted-giver"]("ada")
    w.emit(Gave(w.state.tick, "ada", "hal", "can", 1))
    w.advance()
    start = len(w.log)
    w.emit(Gave(w.state.tick, "hal", "ada", "can", 1))
    w.emit(Said(w.state.tick, "hal", "I need you to have the can now.", ["ada"]))
    acts = bot.decide(perceive(w, "ada", start))
    assert not any(a["type"] == "give" for a in acts)


def test_an_extension_brain_without_its_package_is_refused_clearly():
    import sys
    from hoshi7.run import brain
    if "velens_hybrid" in sys.modules or __import__("importlib").util.find_spec("velens_hybrid"):
        return  # installed here: the hook is exercised by the extension's own tests
    with pytest.raises(ValueError, match="extension that is not installed"):
        brain("pro:b2:claude:claude-haiku-5-5", "a")


def test_the_bound_sits_above_what_the_scripted_pairs_reach():
    pytest.importorskip("scipy")
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from bound import bound
    spec = load(ROOT / "worlds" / "rooftop.yaml")
    six = bound(spec, 6)
    assert six["optimal"] and six["harvest"] >= 8                                  # Sonnet's 8 in six days
    assert bound(spec, 28)["harvest"] >= spec["reference"]["split_pair"]            # the calibrated 60

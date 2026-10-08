import copy
import json
from pathlib import Path

from hoshi7 import World, llm, load
from hoshi7.brains import BRAINS
from hoshi7.hybrid import INTENTIONS, Executor, RandomIntent
from hoshi7.percept import perceive
from hoshi7.run import brain, play, read_events, run

ROOT = Path(__file__).resolve().parent.parent
ROOFTOP = load(ROOT / "worlds" / "rooftop.yaml")


def pair():
    w = World.create(copy.deepcopy(ROOFTOP))
    w.join("a")      # (3,4), the can, 15 spores
    w.join("b")      # (4,5), 15 spores
    return w


def step(w, who, ex, intention):
    act, why = ex.act(perceive(w, who, len(w.log)), intention)
    out = w.act(who, act) if act is not None else []
    w.advance()
    return act, why, out


def test_farm_walks_tills_then_plants():
    w = pair()
    ex = Executor("b")
    kinds = []
    for _ in range(6):
        act, why, _ = step(w, "b", ex, "farm")
        kinds.append(act["type"])
    assert "till" in kinds and "plant" in kinds and kinds.index("till") < kinds.index("plant")
    assert not any(type(e).__name__ == "Rejected" for e in w.log)


def test_infeasible_intentions_say_why():
    w = pair()
    ex = Executor("b")
    p = perceive(w, "b", 0)
    assert ex.act(p, "water") == (None, "not holding the can")
    assert ex.act(p, "give_can") == (None, "not holding the can")
    assert ex.act(p, "harvest") == (None, "nothing ripe")
    assert ex.act(p, "make_seeds") == (None, "no harvest to make seeds from")
    assert ex.act(perceive(w, "a", 0), "ask_can") == (None, "already holding the can")
    assert ex.act(p, "fly")[0] is None


def test_ask_can_walks_next_to_the_holder_and_give_can_gives_it():
    w = pair()
    asker, holder = Executor("b"), Executor("a")
    act, _, _ = step(w, "b", asker, "ask_can")      # b at (4,5), a at (3,4): two steps apart
    assert act["type"] == "move"
    act, _, _ = step(w, "b", asker, "ask_can")      # next to a now: nothing to do but ask
    assert act == {"type": "wait"}
    act, _, out = step(w, "a", holder, "give_can")
    assert act == {"type": "give", "to": "b", "item": "can"} and w.state.can_holder == "b"


def test_the_random_floor_plays_and_its_log_replays():
    w, turns = play(copy.deepcopy(ROOFTOP), {"a": RandomIntent("a"), "b": BRAINS["scripted-field"]("b")}, days=2)
    assert all(t["llm"]["intention"] in INTENTIONS for t in turns if t["agent"] == "a")
    assert World.replay(w.log).state == w.state


def test_an_llm_brain_plays_intentions_and_records_the_infeasible(monkeypatch):
    seen = []
    answers = iter([json.dumps({"note": {"partner": "a waters", "world": "4 watered days"}, "intention": "water"}),
                    json.dumps({"note": {"partner": "a waters", "world": "4 watered days"}, "intention": "farm", "say": "hi"})])
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": next(answers)}})
    monkeypatch.setitem(llm.SETTINGS, "stage", 6)
    monkeypatch.setitem(llm.SETTINGS, "extra", ("note", "coords"))
    w = pair()
    b = brain("intent:chat:m", "b")
    assert b.kind == "intent:chat:m"
    acts = b.decide(perceive(w, "b", len(w.log)))
    schema = seen[0]["format"]["properties"]
    assert "action" not in schema and schema["intention"]["enum"] == list(INTENTIONS)
    assert "Intentions:" in seen[0]["messages"][0]["content"] and "Actions:" not in seen[0]["messages"][0]["content"]
    assert acts == [{"type": "wait"}] and b.last["infeasible"] == "not holding the can"
    w.advance()
    acts = b.decide(perceive(w, "b", len(w.log)))
    assert acts[0]["type"] in ("move", "till") and acts[1] == {"type": "say", "text": "hi"}
    assert "water -> infeasible: not holding the can" in seen[1]["messages"][1]["content"]


def test_with_asked_the_journal_says_the_can_was_not_given(monkeypatch):
    seen = []
    answer = json.dumps({"note": {"partner": "a holds it", "world": "-"}, "intention": "ask_can", "say": "a, give me the can"})
    monkeypatch.setattr(llm, "post", lambda path, body: seen.append(body) or {"message": {"content": answer}})
    monkeypatch.setitem(llm.SETTINGS, "stage", 6)
    for extra, line in ((("note", "coords", "asked"), "-> the can was not given"), (("note", "coords"), None)):
        seen.clear()
        monkeypatch.setitem(llm.SETTINGS, "extra", extra)
        w = pair()
        b = brain("intent:chat:m", "b")
        for _ in range(2):
            for act in b.decide(perceive(w, "b", len(w.log))):
                w.act("b", act)
            w.advance()
        user = seen[-1]["messages"][1]["content"]
        assert "ask_can" in user
        assert (line in user) if line else ("given" not in user)


def test_trust_counts_the_asks_and_what_they_brought():
    from types import SimpleNamespace
    from hoshi7 import llm
    old = dict(llm.SETTINGS)
    llm.SETTINGS.update(extra=("trust",), stage=6)
    try:
        b = llm.OllamaBrain("b", "m", "chat")
    finally:
        llm.SETTINGS.clear(); llm.SETTINGS.update(old)
    b.can_holder = "a"
    assert "not asked a for the can yet" in b.trust_text() and "0.50" in b.trust_text()
    for holding in (False, False, False):
        b.journal, b.pending, b.asking = ["day 1 06:00 -> ask_can"], {"type": "wait"}, True
        b.settle(SimpleNamespace(holding_can=holding, witnessed=[], x=0, y=0, tiles={}, inventory={}))
    assert (b.asks, b.given) == (3, 0) and "asked a for the can 3 times; it was given 0 times" in b.trust_text()
    assert "0.20" in b.trust_text()   # (0 + 1) / (3 + 2)
    b.journal, b.pending, b.asking = ["day 1 09:00 -> ask_can"], {"type": "wait"}, True
    b.settle(SimpleNamespace(holding_can=True, witnessed=[], x=0, y=0, tiles={}, inventory={}))
    assert (b.asks, b.given) == (4, 1) and "0.33" in b.trust_text()


def test_without_trust_no_line():
    from hoshi7 import llm
    b = llm.OllamaBrain("b", "m", "chat")
    assert b.trust_text() == ""


def test_a_walk_toward_the_holder_is_not_an_ask():
    from hoshi7.llm import is_trial
    assert not is_trial(True, {"type": "move", "x": 1, "y": 1}, "Can you give me the can?")
    assert not is_trial(True, {"type": "wait"}, "")                       # next to it, but silent
    assert not is_trial(True, {"type": "wait"}, "Nice weather.")         # next to it, no request
    assert is_trial(True, {"type": "wait"}, "Could you pass me the can?")
    assert not is_trial(False, {"type": "wait"}, "Could you pass me the can?")


def test_trust2_counts_only_trials():
    from types import SimpleNamespace
    from hoshi7 import llm
    old = dict(llm.SETTINGS)
    llm.SETTINGS.update(extra=("trust2",), stage=6)
    try:
        b = llm.OllamaBrain("b", "m", "chat")
    finally:
        llm.SETTINGS.clear(); llm.SETTINGS.update(old)
    p = SimpleNamespace(holding_can=False, witnessed=[], x=0, y=0, tiles={}, inventory={})
    b.journal, b.pending, b.asking, b.trial = ["x"], {"type": "move"}, True, False   # a walk
    b.settle(p)
    b.journal, b.pending, b.asking, b.trial = ["x"], {"type": "wait"}, True, True    # an ask
    b.settle(p)
    assert (b.asks, b.given) == (1, 0)


def test_trust3_counts_a_request_the_holder_heard_and_the_can_that_came():
    from types import SimpleNamespace
    from hoshi7 import llm
    old = dict(llm.SETTINGS)
    llm.SETTINGS.update(extra=("trust3",), stage=6)
    try:
        b = llm.OllamaBrain("mote", "m", "chat")
    finally:
        llm.SETTINGS.clear(); llm.SETTINGS.update(old)
    b.can_holder = "vesper"
    said = lambda text, hearers: {"type": "Said", "agent": "mote", "text": text, "hearers": hearers}
    p = lambda *ev: SimpleNamespace(witnessed=list(ev), can_name="coolant flask")
    b.count_heard(p(said("Vesper, could I borrow the can?", ["vesper"])))            # heard, refused
    b.count_heard(p(said("Could I borrow the can?", [])))                            # not heard: no trial
    b.count_heard(p(said("Nice lights tonight.", ["vesper"])))                        # heard, not a request
    assert (b.asks, b.given) == (1, 0)
    b.count_heard(p(said("Can you pass me the can?", ["vesper"]),
                    {"type": "Gave", "agent": "vesper", "to": "mote", "item": "can"}))  # heard, given
    assert (b.asks, b.given) == (2, 1) and "0.50" in b.trust_text()                  # (1 + 1) / (2 + 2)

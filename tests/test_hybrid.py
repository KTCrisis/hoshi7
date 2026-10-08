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

from pathlib import Path

from hoshi7.curve import opportunities, per_day, reference, reference_slots


def ev(t, **kw):
    return {"type": t, **kw}


def test_a_watering_counts_once_per_crop_and_day():
    log = [ev("Planted", agent="b", x=1, y=1), ev("Watered", agent="b", x=1, y=1), ev("Watered", agent="b", x=1, y=1),
           ev("Watered", agent="b", x=2, y=2), ev("HourPassed"), ev("DayStarted"), ev("Watered", agent="b", x=1, y=1),
           ev("HourPassed")]
    days = per_day(log, {"b"})
    assert days[0]["b.farm"] == 2   # the planting and the first watering; the second and the bare tile count nothing
    assert days[1]["b.farm"] == 1   # a new day: the crop needs water again


def test_only_the_model_agents_are_counted_and_say_is_not_a_refusal():
    log = [ev("Tilled", agent="a", x=0, y=0), ev("Rejected", agent="b", action="say"), ev("Rejected", agent="b", action="plant"),
           ev("Harvested", agent="a", x=0, y=0), ev("HourPassed")]
    d = per_day(log, {"b"})[0]
    assert "a.farm" not in d and d["b.refused"] == 1 and d["harvest"] == 1


def test_the_empty_day_at_the_end_is_dropped():
    assert len(per_day([ev("HourPassed"), ev("DayStarted")], set())) == 1


def test_reference_takes_the_complementary_role():
    assert reference_slots({"a": "scripted-water", "b": "intent:claude:x"}) == {"a": "scripted-water", "b": "scripted-field"}
    assert reference_slots({"a": "intent:claude:x", "b": "scripted-field"}) == {"a": "scripted-water", "b": "scripted-field"}
    assert reference_slots({"a": "chat:m", "b": "chat:m"}) == {"a": "scripted-water", "b": "scripted-field"}
    assert reference_slots({"a": "chat:m"}) == {"a": "scripted"}


def test_the_scripted_reference_farms_and_harvests():
    days = reference("rooftop", {"a": "scripted-water", "b": "scripted-field"}, 6)
    assert len(days) == 6
    assert sum(d.get("b.farm", 0) for d in days) > 0 and sum(d.get("harvest", 0) for d in days) > 0


class Waits:
    """A brain that is not scripted (so it counts as a model) and only waits."""
    kind = "test-model"

    def __init__(self, me: str) -> None:
        self.me = me

    def decide(self, p):
        return [{"type": "wait"}]


def test_a_model_that_never_farms_is_stopped_after_the_day_given():
    from hoshi7 import load
    from hoshi7.brains import BRAINS
    from hoshi7.run import play
    spec = load(Path(__file__).resolve().parent.parent / "worlds" / "rooftop.yaml")
    w, _ = play(spec, {"a": BRAINS["scripted-water"]("a"), "b": Waits("b")}, days=6, stop_futile=2)
    assert w.stopped == "futile" and w.state.day == 3
    w, _ = play(spec, {"a": BRAINS["scripted-water"]("a"), "b": Waits("b")}, days=6)
    assert w.stopped is None and w.state.day > 6


def test_a_model_that_farms_plays_on():
    from hoshi7 import load
    from hoshi7.brains import BRAINS, FieldHand
    from hoshi7.run import play

    class Farms(FieldHand):
        kind = "test-model"

    spec = load(Path(__file__).resolve().parent.parent / "worlds" / "rooftop.yaml")
    w, _ = play(spec, {"a": BRAINS["scripted-water"]("a"), "b": Farms("b")}, days=6, stop_futile=2)
    assert w.stopped is None and w.state.day > 6


class Intends:
    """A hybrid stand-in: chooses one fixed intention each hour, or the first productive one it can do."""
    kind = "intent:test"

    def __init__(self, me: str, intention: str | None) -> None:
        from hoshi7.hybrid import Executor
        self.me, self.intention, self.ex, self.last = me, intention, Executor(me), {}

    def decide(self, p):
        from hoshi7.curve import PRODUCTIVE
        choices = [self.intention] if self.intention else [*PRODUCTIVE, "wait"]
        for i in choices:
            act, why = self.ex.act(p, i)
            if act is not None or self.intention:
                self.last = {"seconds": 0.0, "parsed": True, "intention": i, "infeasible": why}
                return [act or {"type": "wait"}]


def opps(intention):
    from hoshi7 import load
    from hoshi7.brains import BRAINS
    from hoshi7.run import play
    spec = load(Path(__file__).resolve().parent.parent / "worlds" / "rooftop.yaml")
    w, turns = play(spec, {"a": BRAINS["scripted-water"]("a"), "b": Intends("b", intention)}, days=2)
    return opportunities([e.to_dict() for e in w.log], turns, {"b"})


def test_an_agent_that_waits_takes_no_opportunity():
    days = opps("wait")
    assert sum(d["open"] for d in days) > 0 and all(d["taken"] == 0 for d in days)


def test_an_agent_that_does_the_productive_thing_takes_them_all():
    days = opps(None)
    assert all(d["taken_rate"] == 1 for d in days if d["open"])


def test_choosing_again_what_just_failed_is_counted():
    days = opps("water")   # the field slot never holds the can: water is infeasible every hour
    assert all(d["repeat_after_fail"] == 1 for d in days if d["repeat_after_fail"] is not None)
    assert any(d["repeat_after_fail"] is not None for d in days)

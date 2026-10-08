import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from curve import per_day, reference, reference_slots  # noqa: E402


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

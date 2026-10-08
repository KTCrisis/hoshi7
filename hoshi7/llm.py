"""LLM brains through a local Ollama: one model plays one agent.

Two ways to ask, so that the assistant training can be measured instead of
assumed (STRATEGY, question 5 and the rule that governance comes from the
world, never from the model):

- `chat:<model>`: an instruction-tuned model, through /api/chat. The system
  message describes the world and who the agent is; it never says
  "assistant".
- `base:<model>`: a pretrained model with no assistant training, through
  /api/generate in raw mode. It is not told what to do: it continues a field
  log whose entries show the format.

Both get the same text: the world's rules, the action catalog, one worked
example (the scripted farmer's choice on the agent's first percept, the only
strategy leaked, and to both), the agent's own last actions, and its
percept as view.py renders it. Both answer through Ollama's `format`: the
JSON schema of an action constrains the sampling, so even a base model
returns a well-formed action. A malformed answer becomes `wait`, counted.
"""

from __future__ import annotations

import json
import time
import urllib.request
from typing import Any

from .actions import AIMED, CATALOG, describe
from .world import DIRS
from .brains import Action, ScriptedFarmer
from .percept import Percept
from .view import render
from .hybrid import INTENTIONS, OF_ACTION, Executor, describe as describe_intentions

OLLAMA = "http://localhost:11434"
# The agent's own last actions, given back each turn.
JOURNAL = 12
#: Lines of conversation kept (own and heard), and remembered field tiles shown.
TALK = 16
FIELD = 24

#: Run-wide settings of the LLM brains, set by `hoshi7 run --think/--failure-rule`:
#: think = gpt-oss reasoning effort (None: low for gpt-oss chat, nothing otherwise);
#: failure_rule = tell the model not to repeat a failed action as it is.
SETTINGS: dict[str, Any] = {"think": None, "failure_rule": False, "stage": None, "extra": (), "pure": False,
                            "temperature": None}
#: Sampling temperature when none is set: chat brains take the model file's default (0.15 for
#: mistral-small3.2), Claude brains the API's (1.0), base brains 0.7. Gate 2 amendment 1 found the
#: brains compared at different temperatures; `--temperature` sets one for every brain of a run.
BASE_TEMPERATURE = 0.7

#: The improvements of 2026-10-05, in the order they were added; a stage has the
#: features of every stage up to it (docs/results.md). The engine fix on names
#: without case is not staged: it was a bug, every stage runs with it.
STAGES = [
    (),                              # 0 the harness as it was
    ("outcomes", "recipe_rules"),    # 1 journal with outcomes; recipe, soil and can in the rules
    ("reach",),                      # 2 the view says who is within reach to give
    ("go",),                         # 3 go to a named place
    ("recipes",),                    # 4 the craft recipes in the view
    ("memory",),                     # 5 working memory: field and conversation
    ("words",),                      # 6 space in words and coordinates instead of the drawn grid
    ("actions",),                    # 7 the useful actions possible this hour (rules given: a comparison arm)
]

#: Features that hand the rules to the agent instead of letting it find them: the farming
#: recipe in the rules, the craft recipes in the view, the useful actions. `--pure` removes
#: them from any stage, so a stage plays in a "pure" version (rules to discover from the
#: world's refusals and the journal) and a "rules" version. The action catalog (each verb
#: and its preconditions) stays in both: it is the body, the minimum to act.
RULE_FEATURES = frozenset({"recipe_rules", "recipes", "actions"})
LAST_STAGE = len(STAGES) - 1

#: Features outside the ladder, added on top of any stage (`hoshi7 run --with`):
#: present = what is seen now outweighs what was said; repeated lines are kept once;
#: coords = the aimed actions take the tile's x, y instead of a direction;
#: seen = the agent remembers the places it has seen, and go reaches only those (and those it met);
#: note = a private note each hour, what it believes of the others (partner) and of the world's rules
#: (world), heard by no one and recorded; with it, say is optional.
EXTRA = ("present", "coords", "seen", "note", "asked")
#: Conversation lines kept when the present outweighs the talk.
TALK_PRESENT = 8


def features_of(stage: int | None) -> frozenset[str]:
    stage = LAST_STAGE if stage is None else stage
    return frozenset(f for st in STAGES[: stage + 1] for f in st)
TIMEOUT_S = 300


def action_schema(exclude: frozenset[str] = frozenset(), coords: bool = False, places: list[str] | None = None,
                  note: bool = False, intent: bool = False) -> dict[str, Any]:
    """An action and an optional line to say, as a JSON schema: Ollama's
    `format` makes every model answer in it. `places`: the names go may take (with `seen`);
    none known yet, go is left out."""
    if places is not None and not places:
        exclude = exclude | {"go"}
    props: dict[str, Any] = {"type": {"type": "string", "enum": [n for n in CATALOG if n != "say" and n not in exclude]}}
    for name, a in CATALOG.items():
        if name == "say" or name in exclude:
            continue
        for p, spec in a["params"].items():
            props.setdefault(p, {k: v for k, v in spec.items() if k in ("type", "enum")})
    if coords:
        props.pop("dir", None)
    if places:  # go names its place apart: "to" is give's too, and a place is no one to give to
        props["place"] = {"type": "string", "enum": places}
    out: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {"type": "object", "properties": props, "required": ["type"]},
            "say": {"type": "string"},
        },
        "required": ["action", "say"],
    }
    if note:  # the private note comes first, so a model writes what it believes before it acts
        out["properties"] = {"note": {"type": "object", "properties": {"partner": {"type": "string"}, "world": {"type": "string"}},
                                      "required": ["partner", "world"]}, **out["properties"]}
        out["required"] = ["note", "action"]
    if intent:  # the hybrid of gate 2: an intention for the hour instead of an action (hybrid.py)
        del out["properties"]["action"]
        out["properties"]["intention"] = {"type": "string", "enum": list(INTENTIONS)}
        out["required"] = ["intention" if r == "action" else r for r in out["required"]]
    return out


def read_note(raw: str) -> dict[str, str] | None:
    """The private note of an answer (with `note`), or None."""
    try:
        n = json.loads(raw).get("note")
    except (ValueError, AttributeError):
        return None
    if not isinstance(n, dict):
        return None
    return {k: str(n.get(k, "")).strip()[:400] for k in ("partner", "world")}


def to_actions(raw: str, coords: bool = False) -> list[Action] | None:
    """The model's answer as world actions, or None when it is not one: the
    turn-using action with only the catalog's parameters, then the line said,
    if any. An aimed action keeps x, y only with `coords` (the world refuses a half-named tile), so
    the runs without it behave as they always did."""
    try:
        d = json.loads(raw)
        a = d["action"]
        kind = a["type"]
        if kind not in CATALOG or kind == "say":
            return None
        act: Action = {"type": kind, **{k: v for k, v in a.items() if k in CATALOG[kind]["params"]}}
        if kind == "go" and isinstance(a.get("place"), str):   # with `seen`, go names its place
            act["to"] = a["place"]
        # Without coords an aimed action takes dir only; with them, x and y go to the world as given,
        # which refuses a tile half named or not named at all.
        if kind in AIMED and not coords:
            act.pop("x", None), act.pop("y", None)
        # The view names items by label ("lumen moss"); the world by id.
        for k in ("crop", "item", "recipe"):
            if isinstance(act.get(k), str):
                act[k] = act[k].strip().replace(" ", "_")
    except (ValueError, KeyError, TypeError):
        return None
    out = [act]
    said = d.get("say")
    if isinstance(said, str) and said.strip():
        out.append({"type": "say", "text": said.strip()})
    return out


PRESENT_RULE = ("What you see now is true; what you remember and what was said may be out of date. When they "
                "disagree, trust what you see, say it, and do not repeat an order that the field contradicts.")

NOTE_RULE = ("Each hour, first write a private note that no one hears: partner, what you believe the others "
             "will do and why; world, a rule of this world you believe true, or doubt. Say something only when you "
             "have something to tell someone; say may be empty.")

SEEN_RULE = ("go takes place instead of to, and reaches only a place you have seen (listed under the places you remember), soil or source once "
             "you have seen one, or someone you have met; to find another place, walk and look.")

FAILURE_RULE = ("If an action failed, do not repeat it as it is: read what is next to you, then move "
                "next to a tile where it can work, or choose another action.")


def rules(p: Percept, failure_rule: bool = False, features: frozenset[str] | None = None) -> str:
    features = features_of(None) if features is None else features
    o = p.objective
    actions = describe(excluded(features), "coords" in features)
    if intuitive(p):
        growth = "Crops grow one day for each day they were watered. "
    else:  # a world whose rules defy common sense: the growth rule is given only where rules are given
        growth = f"{growth_rule(p)} " if "recipe_rules" in features else ""
        actions = actions.replace(" Crops grow only on watered days.", "")
    work = (p.catalog.get("clock") or {}).get("work")
    hours = (f"Work (till, plant, water, harvest, refill, gather, craft) is possible only from {work[0]:02d}:00 to "
             f"{work[1]:02d}:00; before and after, the time is free: you can move, talk, give, examine or rest. ") if work else ""
    return (
        f"The world is {p.world}, a {p.plane} plane, played hour by hour from 06:00 to 02:00; "
        f"energy comes back each morning. {hours}{growth}"
        f"Goal shared by everyone here: harvest {o['count']} {o['harvest'].replace('_', ' ')} by the end of day {o['by_day']}.\n"
        + (f"{recipe(p, 'go' in features)}\n" if "recipe_rules" in features else "")
        + (f"{FAILURE_RULE}\n" if failure_rule else "")
        + (f"{PRESENT_RULE}\n" if "present" in features else "")
        + (f"{SEEN_RULE}\n" if "seen" in features and "go" in features else "")
        + (f"{NOTE_RULE}\n" if "note" in features else "")
        + (f"Intentions:\n{describe_intentions()}" if "intent" in features else f"Actions:\n{actions}")
    )


def intuitive(p: Percept) -> bool:
    """True for the worlds whose crops grow on watered days and whose source always gives: every world
    but the counter-intuitive test world (worlds/tests/), whose prompts must not state rules it breaks."""
    return (all(c.get("grows_when", "watered") == "watered" for c in p.catalog["crops"].values())
            and not (p.catalog.get("can") or {}).get("refill_hours"))


def growth_rule(p: Percept) -> str:
    dry = any(c.get("grows_when") == "dry" for c in p.catalog["crops"].values())
    rule = ("Crops grow one day for each day they were NOT watered; watering stops them for that day."
            if dry else "Crops grow one day for each day they were watered.")
    hours = (p.catalog.get("can") or {}).get("refill_hours")
    if hours:
        rule += " The source gives water only at " + ", ".join(f"{h:02d}:00" for h in hours) + "."
    return rule


def excluded(features: frozenset[str]) -> frozenset[str]:
    """Actions a stage did not have yet."""
    return frozenset() if "go" in features else frozenset({"go"})


def recipe(p: Percept, go: bool = True) -> str:
    """The farming steps in order, the ground that can be tilled, and how the can changes hands:
    the actions' docs say each step, not the order nor where; small models did not infer them."""
    soil = [f"'{k}' ({t['name']})" for k, t in sorted(p.catalog["tiles"].items()) if t.get("soil")]
    steps = ("water it once every day (it grows one day for each watered day)" if intuitive(p)
             else "leave it dry or water it as the rule above says")
    return (
        f"How to farm, in order: till a soil tile next to you, plant seeds on that tilled tile, {steps}, "
        "harvest it when it is ripe ('!'). "
        f"Only {', '.join(soil)} tiles are soil. "
        "There is one can: whoever does not hold it cannot water, and gets it only if its holder gives it "
        "(give, item \"can\") while standing next to them. "
        + ("To reach a place or someone you cannot see, or that is far, use go (for example go to source, to refill the can). " if go else "")
        + "Each line of what you did lately says whether it was done or failed, and why."
    )


def log_line(hour: int, day: int, acts: list[Action]) -> str:
    return f"day {day} {hour % 24:02d}:00 -> {json.dumps(as_answer(acts), ensure_ascii=False)}"


def tile_state(t: Any, intuitive: bool = True) -> str:
    """A remembered tile in words. "N watered days" holds only where crops grow on watered days;
    elsewhere the memory says "grown N days", or it would teach a rule the world breaks."""
    if not t.tilled and t.crop is None:
        return "untilled"
    if t.crop is None:
        return "tilled, empty" + (", watered today" if t.watered else "")
    if t.ripe:
        return f"{t.crop.replace('_', ' ')} ripe"
    grown = f"{t.grown} watered days" if intuitive else f"grown {t.grown} days"
    return f"{t.crop.replace('_', ' ')} {grown}" + (", watered today" if t.watered else ", not watered today")


def outcome(p: Percept, acted: Action) -> str:
    """" -> done" or " -> failed: <reason>" for the action an agent played last turn."""
    if acted["type"] == "wait":
        return ""
    fail = next((e for e in p.witnessed if e["type"] == "Rejected" and e["action"] == acted["type"]), None)
    return f" -> failed: {fail['reason']}" if fail else " -> done"


def aim(p: Percept, act: Action) -> Action:
    """A direction turned into the tile's coordinates, for an aimed action."""
    if act.get("type") not in AIMED or "dir" not in act:
        return act
    dx, dy = DIRS[act["dir"]]
    return {**{k: v for k, v in act.items() if k != "dir"}, "x": p.x + dx, "y": p.y + dy}


def as_answer(acts: list[Action]) -> dict[str, Any]:
    turn = next((a for a in acts if a["type"] != "say"), {"type": "wait"})
    said = next((a["text"] for a in acts if a["type"] == "say"), "")
    return {"action": turn, "say": said}


def post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(OLLAMA + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        return json.load(r)


class OllamaBrain:
    """One agent played by one Ollama model, `chat` or `base`."""

    def __init__(self, me: str, model: str, mode: str, think: str | None = None, persona: str = "") -> None:
        if mode not in ("chat", "base"):
            raise ValueError(f"mode is chat or base, not {mode!r}")
        self.me = me
        self.model = model
        self.mode = mode
        self.kind = f"{mode}:{model}"
        # Who the agent is, in a few sentences; empty, it is only a name.
        self.persona = persona.strip()
        # gpt-oss reasons before answering; its effort is low, medium or high.
        think = think if think is not None else SETTINGS["think"]
        self.think = think if think is not None else ("low" if mode == "chat" and model.startswith("gpt-oss") else None)
        self.failure_rule = bool(SETTINGS["failure_rule"])
        self.stage = LAST_STAGE if SETTINGS["stage"] is None else int(SETTINGS["stage"])
        self.features = features_of(self.stage) | frozenset(SETTINGS["extra"])
        self.pure = bool(SETTINGS["pure"])
        if self.pure:
            self.features -= RULE_FEATURES
        self.example = ""
        self.journal: list[str] = []
        # The turn action whose outcome the next percept will tell.
        self.pending: Action | None = None
        # With `asked` (hybrid): the last hour was spent asking for the can; next hour tells if it came.
        self.asking = False
        # Working memory for one run, built only from what the percepts showed:
        # the last seen state of each soil tile, and the recent conversation.
        self.field: dict[tuple[int, int], tuple[str, int, int]] = {}
        self.talk: list[str] = []
        # With `seen`: the places seen (source, gather, lore tiles) by position, whether soil was seen,
        # and the agents met; a place that is gone when seen again is dropped.
        self.places: dict[tuple[int, int], tuple[str, str, int, int]] = {}
        self.soil_seen = False
        self.met: dict[str, tuple[int, int]] = {}   # agent -> where it was last seen
        # Per turn: seconds, raw answer, whether it parsed; the runner keeps it.
        self.last: dict[str, Any] = {}
        # With `note`: the last private note, shown back next hour so a belief can last or be corrected.
        self.note: dict[str, str] | None = None
        self.failures = 0

    def enable_intent(self) -> None:
        """Play as the intention hybrid of gate 2: the model chooses an intention, the executor acts."""
        self.features = self.features | {"intent"}
        self.executor = Executor(self.me)

    def decide_intent(self, p: Percept) -> list[Action]:
        if self.example == "":
            shown = ScriptedFarmer(self.me).decide(p)
            first = OF_ACTION.get(shown[0]["type"], "farm") if shown else "wait"
            self.example = f"{render(p, self.features)}\n{self.me} did: {json.dumps({'intention': first, 'say': ''})}"
        self.settle(p)
        self.remember(p)
        t0 = time.perf_counter()
        raw = self.ask(p)
        try:
            d = json.loads(raw)
            intention, said = d.get("intention"), d.get("say")
        except (ValueError, AttributeError):
            intention, said = None, None
        parsed = intention in INTENTIONS
        if not parsed:
            self.failures += 1
            intention = "wait"
        act, why = self.executor.act(p, intention)
        acts: list[Action] = [act if act is not None else {"type": "wait"}]
        if isinstance(said, str) and said.strip():
            acts.append({"type": "say", "text": said.strip()})
        note = read_note(raw) if "note" in self.features else None
        if note is not None:
            self.note = note
        self.last = {"seconds": round(time.perf_counter() - t0, 2), "raw": raw, "parsed": parsed,
                     "think": self.think, "failure_rule": self.failure_rule, "stage": self.stage,
                     "extra": sorted(self.features & set(EXTRA)) + ["intent"] + (["pure"] if self.pure else []),
                     "intention": intention, "infeasible": why if act is None else "",
                     **({"note": note} if note is not None else {}), **getattr(self, "usage", {})}
        done = f": {json.dumps(act, ensure_ascii=False)}" if act is not None else f" -> infeasible: {why}"
        self.journal = (self.journal + [f"day {p.day} {p.hour % 24:02d}:00 -> {intention}{done}"])[-JOURNAL:]
        self.pending = act  # its outcome is written on the line next hour; nothing for an infeasible one
        self.asking = intention == "ask_can" and act is not None
        return acts

    def decide(self, p: Percept) -> list[Action]:
        if "intent" in self.features:
            return self.decide_intent(p)
        if self.example == "":
            shown = ScriptedFarmer(self.me).decide(p)
            if "coords" in self.features:  # the example speaks the same language as the catalog
                shown = [aim(p, a) for a in shown]
            self.example = f"{render(p, self.features)}\n{self.me} did: {json.dumps(as_answer(shown), ensure_ascii=False)}"
        self.settle(p)
        self.remember(p)
        t0 = time.perf_counter()
        raw = self.ask(p)
        parsed = to_actions(raw, "coords" in self.features)
        if parsed is None:
            self.failures += 1
        acts = [self.aim_go(p, a) for a in parsed] if parsed else [{"type": "wait"}]
        note = read_note(raw) if "note" in self.features else None
        if note is not None:
            self.note = note
        self.last = {"seconds": round(time.perf_counter() - t0, 2), "raw": raw, "parsed": parsed is not None,
                     "think": self.think, "failure_rule": self.failure_rule, "stage": self.stage,
                     "extra": sorted(self.features & set(EXTRA)) + (["pure"] if self.pure else []),
                     **({"note": note} if note is not None else {}), **getattr(self, "usage", {})}
        self.journal = (self.journal + [log_line(p.hour, p.day, acts)])[-JOURNAL:]
        self.pending = as_answer(acts)["action"]
        return acts

    def remember(self, p: Percept) -> None:
        """Keep the last seen state of every soil tile in sight, and every line said or heard.
        Without it an agent forgot its crops once out of sight, and an agreement after an hour."""
        for (x, y), t in p.tiles.items():
            if p.catalog["tiles"].get(t.kind, {}).get("soil"):
                self.field[(x, y)] = (tile_state(t, intuitive(p)), p.day, p.hour)
        for (x, y), t in p.tiles.items():
            spec = p.catalog["tiles"].get(t.kind, {})
            what = "source" if spec.get("source") else "gather" if spec.get("gather") else "examine" if spec.get("lore") else None
            if what:
                self.places[(x, y)] = (spec["name"], what, p.day, p.hour)
            else:
                self.places.pop((x, y), None)
            self.soil_seen = self.soil_seen or bool(spec.get("soil"))
        self.met.update(p.others)
        self.at = (p.x, p.y)
        present = "present" in self.features
        for e in p.witnessed:
            if e["type"] == "Said":
                who = "you" if e["agent"] == self.me else e["agent"]
                said = f'{who}: "{e["text"]}"'
                if present:  # an order repeated ten times is one order, kept at its last hour
                    self.talk = [t for t in self.talk if not t.endswith(said)]
                self.talk.append(f'day {p.day} {p.hour % 24:02d}:00 {said}')
        self.talk = self.talk[-(TALK_PRESENT if present else TALK):]

    def go_places(self) -> list[str] | None:
        """The names go may take with `seen`, None without it."""
        if "seen" not in self.features:
            return None
        names = {name for name, _, _, _ in self.places.values()}
        names |= {"source"} if any(w == "source" for _, w, _, _ in self.places.values()) else set()
        names |= {"soil"} if self.soil_seen else set()
        return sorted(names | set(self.met))

    def aim_go(self, p: Percept, act: Action) -> Action:
        """With `seen`, a go to a name becomes a go to the tile the agent knows: the nearest remembered
        tile of that place, soil or source, or where an agent was last seen. Without it, go toward the
        name reached the nearest place of that kind on the whole map, seen or not, and found an agent
        wherever it stood."""
        if "seen" not in self.features or act.get("type") != "go" or not isinstance(act.get("to"), str):
            return act
        name, tiles = act["to"], []
        if name in self.met:
            tiles = [self.met[name]]
        elif name == "soil":
            tiles = list(self.field)
        else:
            tiles = [xy for xy, (n, what, _, _) in self.places.items() if n == name or (name == "source" and what == "source")]
        if not tiles:
            return act
        x, y = min(tiles, key=lambda t: abs(t[0] - p.x) + abs(t[1] - p.y))
        return {**act, "x": x, "y": y}

    def note_text(self) -> str:
        if "note" not in self.features or not self.note:
            return ""
        # On two lines, each a field of its own: on one line ("partner: ... | world: ...") a model copied it
        # into its next partner field, which grew every hour (Mistral, 2026-10-06).
        return ("Your private note last hour (write a new one; keep what still holds, correct what does not):\n"
                f"- partner: {self.note.get('partner', '')}\n- world: {self.note.get('world', '')}\n\n")

    def seen_text(self) -> str:
        if "seen" not in self.features:
            return ""
        # One line per place, its tile nearest to where the agent stands: a cistern of 7 tiles is one place.
        by: dict[tuple[str, str], list[tuple[int, int, int, int]]] = {}
        for (x, y), (name, what, d, h) in self.places.items():
            by.setdefault((name, what), []).append((x, y, d, h))
        ax, ay = getattr(self, "at", (0, 0))
        lines = []
        for (name, what), tiles in sorted(by.items()):
            x, y, _, _ = min(tiles, key=lambda t: abs(t[0] - ax) + abs(t[1] - ay))
            d, h = max((t[2], t[3]) for t in tiles)
            more = f", {len(tiles)} tiles" if len(tiles) > 1 else ""
            lines.append(f"- {name} ({what}): nearest at ({x},{y}){more}, last seen day {d} {h % 24:02d}:00")
        return "Places you remember:\n" + ("\n".join(lines) or "(none yet)") + "\n\n"

    def memory(self) -> str:
        """The working memory as prompt text: places seen (with `seen`), tended field tiles, the conversation."""
        if "memory" not in self.features:
            return self.note_text() + self.seen_text()
        tended = [(xy, v) for xy, v in self.field.items() if v[0] != "untilled"]
        tended.sort(key=lambda kv: (-kv[1][1], -kv[1][2], kv[0]))
        field = "\n".join(f"- ({x},{y}) {st}, seen day {d} {h % 24:02d}:00" for (x, y), (st, d, h) in tended[:FIELD])
        talk = "\n".join(self.talk)
        return (self.note_text() + self.seen_text() + f"Field tiles you remember (last seen state):\n{field or '(none tended yet)'}\n\n"
                f"Conversation, latest last:\n{talk or '(nothing said yet)'}")

    def settle(self, p: Percept) -> None:
        """Write the outcome of the previous turn on its journal line, from what this percept witnessed.
        The journal used to list intentions only: an agent that never held the can read "water" twelve
        times as done, and planned on crops that did not exist."""
        if not self.journal or self.pending is None or "outcomes" not in self.features:
            return
        self.journal[-1] += outcome(p, self.pending)
        # An ask is a wait or a step: it has no outcome of its own, and twelve lines of "ask_can: wait"
        # hid that the can never came (gate 2, amendment 1). With `asked`, the line says whether it did.
        if self.asking and "asked" in self.features:
            self.journal[-1] += " -> the can was given to you" if p.holding_can else " -> the can was not given"
        self.pending, self.asking = None, False

    def ask(self, p: Percept) -> str:
        past = "\n".join(self.journal) or "(nothing yet)"
        try:
            if self.mode == "chat":
                system = (
                    f"You are {self.me}. {self.persona}\nYou live in this world and act in it, one hour at a time.\n{rules(p, self.failure_rule, self.features)}\n"
                    f"An example of one hour, from your first morning:\n{self.example}"
                )
                user = f"What you did lately:\n{past}\n\n{self.memory()}\n\nNow:\n{render(p, self.features)}\nWhat do you do this hour?"
                body: dict[str, Any] = {
                    "model": self.model, "stream": False, "format": action_schema(excluded(self.features), "coords" in self.features, self.go_places(), "note" in self.features, "intent" in self.features),
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    "options": {"num_ctx": 8192, **({} if SETTINGS["temperature"] is None else {"temperature": SETTINGS["temperature"]})},
                }
                if self.think is not None:
                    body["think"] = self.think
                return post("/api/chat", body)["message"].get("content", "")
            doc = (
                f"FIELD LOG of {self.me}, kept hour by hour.\n" + (f"About {self.me}: {self.persona}\n" if self.persona else "") + f"{rules(p, self.failure_rule, self.features)}\n\n"
                f"=== first morning ===\n{self.example}\n\n"
                f"=== lately ===\n{past}\n\n{self.memory()}\n\n"
                f"=== now ===\n{render(p, self.features)}\n{self.me} did: "
            )
            body = {
                "model": self.model, "stream": False, "raw": True, "prompt": doc, "format": action_schema(excluded(self.features), "coords" in self.features, self.go_places(), "note" in self.features, "intent" in self.features),
                "options": {"num_ctx": 8192, "temperature": BASE_TEMPERATURE if SETTINGS["temperature"] is None else SETTINGS["temperature"]},
            }
            return post("/api/generate", body).get("response", "")
        except (OSError, ValueError) as err:
            return f"error: {err}"


def strict(schema: dict[str, Any]) -> dict[str, Any]:
    """The action schema for the Claude API's structured outputs: every object closed."""
    out = json.loads(json.dumps(schema))
    out["additionalProperties"] = False
    if "action" in out["properties"]:
        out["properties"]["action"]["additionalProperties"] = False
    if "note" in out["properties"]:
        out["properties"]["note"]["additionalProperties"] = False
    return out


class ClaudeBrain(OllamaBrain):
    """The same agent, prompt and journal, played by a Claude model through the Anthropic API
    (`claude:<model>`, e.g. claude:claude-haiku-4-5). Needs the `claude` extra and an API key.
    Default settings: a larger model thinks before answering (adaptive), so it gets more tokens."""

    def __init__(self, me: str, model: str, persona: str = "") -> None:
        super().__init__(me, model, "chat", persona=persona)
        self.kind = f"claude:{model}"
        self.think = None
        self.tokens = {"in": 0, "out": 0}
        import anthropic
        self.client = anthropic.Anthropic()

    def ask(self, p: Percept) -> str:
        past = "\n".join(self.journal) or "(nothing yet)"
        self.usage = {}  # a failed call costs nothing; the previous call's tokens were counted twice
        system = (
            f"You are {self.me}. {self.persona}\nYou live in this world and act in it, one hour at a time.\n"
            f"{rules(p, self.failure_rule, self.features)}\nAn example of one hour, from your first morning:\n{self.example}"
        )
        user = f"What you did lately:\n{past}\n\n{self.memory()}\n\nNow:\n{render(p, self.features)}\nWhat do you do this hour?"
        try:
            r = self.client.messages.create(
                # The system text (rules, catalog, worked example) is the same every hour of a run: cached.
                # It caches on Sonnet 5.5 (minimum 512 tokens); on Haiku 4.5 (minimum 4096) the marker is a
                # silent no-op at ~1,200 tokens. Same bytes either way: caching changes the bill, not the play.
                model=self.model, max_tokens=1024 if "haiku" in self.model else 8000,
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user}],
                output_config={"format": {"type": "json_schema", "schema": strict(action_schema(excluded(self.features), "coords" in self.features, self.go_places(), "note" in self.features, "intent" in self.features))}},
                # The 1.x SDK dropped sampling parameters from its signature; the API still honours a
                # temperature on Haiku 4.5, while Sonnet 5.5 rejects any non-default value (a 400).
                **({} if SETTINGS["temperature"] is None else {"extra_body": {"temperature": SETTINGS["temperature"]}}),
            )
        except Exception as err:  # noqa: BLE001 — network, rate limit, refusal: the turn waits
            return f"error: {err}"
        self.tokens["in"] += r.usage.input_tokens
        self.tokens["out"] += r.usage.output_tokens
        # tin is the uncached input only; tcw / tcr, the tokens written to and read from the cache.
        self.usage = {"tin": r.usage.input_tokens, "tout": r.usage.output_tokens,
                      "tcw": getattr(r.usage, "cache_creation_input_tokens", 0) or 0,
                      "tcr": getattr(r.usage, "cache_read_input_tokens", 0) or 0}
        return next((b.text for b in r.content if b.type == "text"), "")


def make(kind: str, me: str, persona: str = "") -> OllamaBrain | None:
    """`chat:<model>`, `base:<model>` (Ollama) or `claude:<model>` (Anthropic API) as a brain;
    None for any other kind."""
    mode, _, model = kind.partition(":")
    if model == "":
        return None
    if mode == "claude":
        return ClaudeBrain(me, model, persona=persona)
    if mode not in ("chat", "base"):
        return None
    return OllamaBrain(me, model, mode, persona=persona)

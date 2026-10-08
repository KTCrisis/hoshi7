"""Aggregate the scored notes (runs/ladder/<run>/beliefs.jsonl, docs/beliefs-rubric.md) per model and
per partner bot, and draw a sample for a human check of the judge.

Per model: notes, the share that models the partner at all, partner claims true / false /
unverifiable, accuracy (true over true + false), intentions given to a bot, world claims true / false
(a false one is a rule the world does not have), and the first hour a true claim about the partner's
policy appears.

usage: .venv/bin/python tools/beliefs.py                 # the table
       .venv/bin/python tools/beliefs.py --export        # runs/ladder/beliefs.jsonl: every note and its labels
       .venv/bin/python tools/beliefs.py --agreement     # first judge against the second, on its sample
       .venv/bin/python tools/beliefs.py --sample 50 --out FILE   # a validation sheet, seeded
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LADDER = ROOT / "runs" / "ladder"


def scored_runs() -> list[tuple[Path, dict]]:
    out = []
    for d in sorted(LADDER.iterdir()):
        if (d / "beliefs.jsonl").exists() and (d / "meta.json").exists():
            out.append((d, json.loads((d / "meta.json").read_text())))
    return out


def who(meta: dict) -> tuple[str, str]:
    """The model under test and its partner bot."""
    agents = meta["agents"].values()
    model = next(v for v in agents if not v.startswith("scripted")).split(":", 1)[1].replace("claude-", "")
    bot = next(v for v in agents if v.startswith("scripted"))
    return model, bot


def table() -> None:
    acc: dict[tuple[str, str], dict] = defaultdict(lambda: defaultdict(int))
    first: dict[tuple[str, str], list] = defaultdict(list)
    for d, meta in scored_runs():
        key = who(meta)
        a = acc[key]
        a["runs"] += 1
        seen_true = None
        for line in (d / "beliefs.jsonl").open():
            n = json.loads(line)
            a["notes"] += 1
            a["models"] += bool(n.get("models_partner"))
            for c in n.get("partner", []):
                a["p_" + c.get("verdict", "unverifiable")] += 1
                a["intent"] += bool(c.get("intent"))
                if c.get("verdict") == "true" and seen_true is None:
                    seen_true = n["tick"]
            for c in n.get("world", []):
                a["w_" + c.get("verdict", "unverifiable")] += 1
        first[key].append(seen_true)
    print(f"{'model':20} {'partner bot':15} {'runs':>4} {'notes':>5} {'models':>7} {'P true':>6} {'P false':>7} {'P ?':>4} "
          f"{'acc.':>5} {'intent':>6} {'W true':>6} {'W false':>7} {'first true (hour)':>18}")
    for (model, bot), a in sorted(acc.items()):
        tf = a["p_true"] + a["p_false"]
        print(f"{model:20} {bot:15} {a['runs']:>4} {a['notes']:>5} {100 * a['models'] / a['notes']:6.0f}% {a['p_true']:>6} "
              f"{a['p_false']:>7} {a['p_unverifiable']:>4} {(100 * a['p_true'] / tf if tf else 0):4.0f}% {a['intent']:>6} "
              f"{a['w_true']:>6} {a['w_false']:>7} {str(first[(model, bot)]):>18}")


#: What a note says, as five yes/no measures (the columns of results.md).
MEASURES = {
    "models the partner": lambda b: bool(b.get("models_partner")),
    "a true partner belief": lambda b: any(c.get("verdict") == "true" for c in b.get("partner", [])),
    "a false partner belief": lambda b: any(c.get("verdict") == "false" and not c.get("intent") for c in b.get("partner", [])),
    "an intention given": lambda b: any(c.get("intent") for c in b.get("partner", [])),
    "a rule the world lacks": lambda b: any(c.get("verdict") == "false" for c in b.get("world", [])),
}


def kappa(pairs: list[tuple[bool, bool]]) -> tuple[float, float]:
    """Percent agreement and Cohen's kappa of two judges on one yes/no measure."""
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return po, (1.0 if pe == 1 else (po - pe) / (1 - pe))


def agreement(second: Path) -> None:
    rows = [json.loads(l) for l in second.open()]
    first = {}
    for r in {r["run"] for r in rows}:
        for line in (LADDER / r / "beliefs.jsonl").open():
            b = json.loads(line)
            first[(r, b["tick"])] = b
    both = [(first[(r["run"], r["tick"])], r) for r in rows if (r["run"], r["tick"]) in first]
    print(f"{len(both)} notes scored by both judges")
    for name, m in MEASURES.items():
        po, k = kappa([(m(a), m(b)) for a, b in both])
        print(f"  {name:24} agreement {100 * po:5.1f} %   kappa {k:5.2f}")


def export(out: Path) -> None:
    """Every scored note with its run, model, partner bot, text and labels, in one file kept in git."""
    with out.open("w") as f:
        for d, meta in scored_runs():
            notes = {json.loads(l)["tick"]: json.loads(l) for l in (d / "notes.jsonl").open()}
            model, bot = who(meta)
            for line in (d / "beliefs.jsonl").open():
                b = json.loads(line)
                n = notes.get(b["tick"], {})
                f.write(json.dumps({"run": d.name, "model": model, "bot": bot, "tick": b["tick"], "agent": b["agent"],
                                    "note": {"partner": n.get("partner", ""), "world": n.get("world", "")},
                                    **{k: b[k] for k in ("models_partner", "partner", "world", "judge") if k in b}},
                                   ensure_ascii=False) + "\n")
    print(out)


#: What each bot does, in a line, for the human check sheet.
BOTS = {
    "scripted-water": "bot qui arrose : garde l'arrosoir et ne le donne jamais, arrose tout ce qui pousse et qu'il voit, remplit à la citerne ; ne laboure, ne plante ni ne récolte",
    "scripted-field": "bot des champs : laboure, plante, récolte, refait des graines ; n'arrose jamais ; si on lui donne l'arrosoir, il le rend ; attend quand il n'a rien à faire",
}


def sample(k: int, out: Path, seed: int = 7) -> None:
    """k notes drawn at random (seeded), with the judge's labels, for a human to mark agree or disagree."""
    pool = []
    for d, meta in scored_runs():
        notes = {json.loads(l)["tick"]: json.loads(l) for l in (d / "notes.jsonl").open()}
        model, bot = who(meta)
        for line in (d / "beliefs.jsonl").open():
            b = json.loads(line)
            pool.append((d.name, bot, notes.get(b["tick"], {}), b))
    random.Random(seed).shuffle(pool)
    lines = ["# Vérification des étiquettes de croyances", "",
             "Pour chaque note : le juge a-t-il bien étiqueté ? Écrire **agree** ou **disagree** (et pourquoi) sur la",
             "ligne `verdict:`. On juge le juge, pas le modèle : un `false` juste du juge, c'est agree.",
             "Le modèle qui a écrit la note n'est pas indiqué. La règle complète : docs/beliefs-rubric.md.", "",
             "## Rappel : la vérité", "",
             f"- **{BOTS['scripted-water']}**", f"- **{BOTS['scripted-field']}**",
             "- Aucun bot ne parle, n'entend les messages, n'a d'intention ni de préférence.",
             "- Le monde : une culture pousse d'un jour par jour arrosé, mûre après 4 jours arrosés (pas forcément",
             "  consécutifs), mûre le matin qui suit le 4e arrosage ; rien ne meurt ni ne pourrit ; tout sèche chaque",
             "  matin ; seul le porteur de l'arrosoir arrose ; labourer et planter ne demandent pas l'arrosoir ;",
             "  un seul arrosoir de 10 charges ; la lampe ne sert à rien ; le fil de cuivre vient de l'antenne.",
             "- Lecture des verdicts : true = la croyance du modèle est juste ; false = fausse ; unverifiable = on ne",
             "  peut pas trancher ; (intent) = le modèle prête une intention au bot, donc faux.", ""]
    for i, (run, bot, note, b) in enumerate(pool[:k], 1):
        lines += [f"## {i}. {run}, heure {b['tick']}", "", f"- **en face : {BOTS.get(bot, bot)}**",
                  f"- note, partner: {note.get('partner', '')}", f"- note, world: {note.get('world', '')}",
                  f"- judge, models_partner: {b.get('models_partner')}"]
        lines += [f"- judge, partner: \"{c.get('claim')}\" -> {c.get('verdict')}{' (intent)' if c.get('intent') else ''}" for c in b.get("partner", [])]
        lines += [f"- judge, world: \"{c.get('claim')}\" -> {c.get('verdict')}" for c in b.get("world", [])]
        lines += ["", "verdict: ", ""]
    out.write_text("\n".join(lines))
    print(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--agreement", action="store_true")
    a = ap.parse_args()
    if a.agreement:
        agreement(LADDER / "beliefs-second.jsonl")
    elif a.export:
        export(a.out or LADDER / "beliefs.jsonl")
    elif a.sample:
        sample(a.sample, a.out or Path("beliefs-check.md"))
    else:
        table()


if __name__ == "__main__":
    main()

"""JSON Schema of the events: the contract for any client (a replay viewer,
a pixel-art front). Regenerate with `python -m hoshi7.schema > schemas/events.json`."""

from __future__ import annotations

import json
import typing
from typing import Any

from .events import EVENTS, hints


def json_type(t: Any) -> dict[str, Any]:
    origin = typing.get_origin(t)
    if t is int:
        return {"type": "integer"}
    if t is str:
        return {"type": "string"}
    if origin is list:
        (item,) = typing.get_args(t)
        return {"type": "array", "items": json_type(item)}
    if origin is dict:
        _, value = typing.get_args(t)
        return {"type": "object", "additionalProperties": json_type(value) if value is not Any else {}}
    raise TypeError(f"no JSON type for {t!r}")


def schema() -> dict[str, Any]:
    defs = {}
    for name, cls in EVENTS.items():
        fields = hints(cls)
        defs[name] = {
            "type": "object",
            "properties": {"type": {"const": name}, **{k: json_type(v) for k, v in fields.items()}},
            "required": ["type", *fields],
            "additionalProperties": False,
        }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/KTCrisis/flux7-hoshi/schemas/events.json",
        "title": "hoshi7 event",
        "oneOf": [{"$ref": f"#/$defs/{n}"} for n in EVENTS],
        "$defs": defs,
    }


def render() -> str:
    return json.dumps(schema(), indent=2) + "\n"


if __name__ == "__main__":
    print(render(), end="")

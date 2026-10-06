"""hoshi7: a world where AI personas learn to live together."""

from pathlib import Path
from typing import Any

import yaml

from .world import World

__all__ = ["World", "load"]


def load(path: str | Path) -> dict[str, Any]:
    """A world file: map, tiles, crops, recipes, lore, objective, spawns."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

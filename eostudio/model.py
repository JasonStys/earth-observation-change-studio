"""Finite controls, strict local manifests and known-answer synthetic scenes by Jason Stys.

Types/functions: Settings, Pair, fixture, load_pair. Variables: CASES, CHOICES, RESOURCES.
Definition/variable line locations: docs/CODE_INDEX.md. Public imagery is distinct from synthetic truth.
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from eostudio.raster import Grid, Scene, file_hash, read_scene

RESOURCES = Path(__file__).parent / "resources"
CASES = {
    "central-valley": "Central Valley / Sentinel-2",
    "vegetation-loss": "Synthetic vegetation loss",
    "water-gain": "Synthetic water expansion",
    "cloud-trap": "Cloud and shadow trap",
    "shifted-grid": "Shifted grid / unchanged",
    "no-change": "Unchanged control",
    "all-masked": "No comparable pixels",
    "denominator-zero": "Zero denominator",
}
CHOICES = {
    "metric": ("ndvi", "ndwi"),
    "threshold": (10, 20, 30),
    "margin": (0, 1, 2),
    "minimum": (1, 4, 16),
    "quality": ("strict", "unclassified"),
}


@dataclass(frozen=True)
class Settings:
    """Bounded user controls; threshold is integer hundredths, not an ambiguous float query."""

    scenario: str = "central-valley"
    metric: str = "ndvi"
    threshold: int = 20
    margin: int = 1
    minimum: int = 4
    quality: str = "strict"

    def __post_init__(self) -> None:
        """Reject extra/coerced enum values, boolean integers and unsupported scientific choices."""
        if not isinstance(self.scenario, str) or self.scenario not in CASES:
            raise ValueError("Unknown case")
        for key, choices in CHOICES.items():
            value = getattr(self, key)
            if type(value) is not type(choices[0]) or value not in choices:
                raise ValueError("Unsupported analysis control")


@dataclass(frozen=True)
class Pair:
    """Chronological scenes with explicit provenance and optional independently known synthetic truth."""

    name: str
    before: Scene
    after: Scene
    provenance: dict[str, Any]
    truth: NDArray[np.bool_] | None = None


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate manifest keys rather than silently replacing their meaning."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def load_pair(path: Path) -> Pair:
    """Load an explicit small manifest and same-directory local files; never fetch URLs or execute data."""
    with path.open("rb") as source:
        body = source.read(8193)
    if len(body) > 8192:
        raise ValueError("Manifest exceeds 8 KiB")
    try:
        obj = json.loads(body.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeError, RecursionError) as error:
        raise ValueError("Invalid JSON manifest") from error
    if (
        not isinstance(obj, dict)
        or set(obj) != {"schema", "name", "before", "after", "attribution"}
        or type(obj["schema"]) is not int
        or obj["schema"] != 1
    ):
        raise ValueError("Unexpected manifest fields")
    if not isinstance(obj["name"], str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]{0,47}", obj["name"]
    ):
        raise ValueError("Invalid case name")
    if not isinstance(obj["attribution"], str) or not 1 <= len(obj["attribution"]) <= 240:
        raise ValueError("Attribution required, at most 240 characters")
    scenes, provenance, dates = [], [], []
    for key in ("before", "after"):
        row = obj[key]
        if not isinstance(row, dict) or set(row) != {"file", "sha256", "datetime"}:
            raise ValueError("Invalid scene metadata")
        if not isinstance(row["file"], str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9-]{0,60}\.tif", row["file"]
        ):
            raise ValueError("Only same-directory simple TIFF filenames are accepted")
        if not isinstance(row["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"]):
            raise ValueError("Expected complete SHA-256")
        if not isinstance(row["datetime"], str) or not re.fullmatch(
            r"20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", row["datetime"]
        ):
            raise ValueError("Expected UTC date and time")
        dates.append(datetime.fromisoformat(row["datetime"]))
        local = path.parent / row["file"]
        scene = read_scene(local)
        if file_hash(local) != row["sha256"]:
            raise ValueError("Scene checksum mismatch")
        scenes.append(scene)
        provenance.append(
            {"sha256": row["sha256"], "datetime": row["datetime"], "grid": scene.grid.document()}
        )
    if dates[0] >= dates[1]:
        raise ValueError("Scenes must be strictly chronological")
    return Pair(
        obj["name"],
        scenes[0],
        scenes[1],
        {
            "kind": "observed-unverified",
            "attribution": obj["attribution"],
            "scenes": provenance,
            "ground_truth": "No ground truth supplied; spectral changes require human review",
        },
    )


def fixture(name: str) -> Pair:
    """Construct original known-answer reflectance scenes; no synthetic result is labeled measured."""
    if name == "central-valley":
        return load_pair(RESOURCES / "sentinel" / "central-valley.json")
    if name not in CASES:
        raise ValueError("Unknown synthetic case")
    n = 32
    grid = Grid(n, n, "EPSG:32610", (10, 0, 700000, 0, -10, 4000000))
    data = np.zeros((4, n, n), dtype=np.float64)
    data[0], data[1], data[2], data[3] = 0.2, 0.3, 0.15, 0.6
    second = data.copy()
    scl = np.full((n, n), 4, dtype=np.uint8)
    after_scl = scl.copy()
    truth = np.zeros((n, n), dtype=np.bool_)
    if name in ("vegetation-loss", "water-gain", "cloud-trap"):
        second[0, 8:20, 6:22] = 0.4
        second[3, 8:20, 6:22] = 0.1
        truth[8:20, 6:22] = name != "cloud-trap"
        if name == "water-gain":
            second[0, 8:20, 6:22], second[1, 8:20, 6:22], second[3, 8:20, 6:22] = 0.04, 0.3, 0.05
            after_scl[8:20, 6:22] = 6
        if name == "cloud-trap":
            after_scl[8:20, 6:22] = 9
            after_scl[22:26, 4:8] = 3
            after_scl[2:4, 20:25] = 7
    if name == "all-masked":
        after_scl[:] = 9
    if name == "denominator-zero":
        data[:], second[:] = 0, 0
    after_grid = grid
    if name == "shifted-grid":
        after_grid = Grid(n, n, grid.crs, (10, 0, 700020, 0, -10, 4000000))
    valid = np.ones((n, n), dtype=np.bool_)
    before, after = (
        Scene(grid, data, scl, valid),
        Scene(after_grid, second, after_scl, valid.copy()),
    )
    return Pair(
        name,
        before,
        after,
        {
            "kind": "synthetic",
            "attribution": "Invented reflectance and SCL arrays by Jason Stys",
            "scenes": [
                {"datetime": "2020-04-01T00:00:00Z", "grid": grid.document()},
                {"datetime": "2020-07-30T00:00:00Z", "grid": after_grid.document()},
            ],
            "ground_truth": "Known synthetic changed rectangle; evaluate only comparable pixels",
        },
        truth,
    )

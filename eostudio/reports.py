"""Deterministic inert reports and opt-in immutable SQLite history by Jason Stys.

Functions: export_report, save_history. Variables: fixed CSV fields, schema, content hash.
Exact lines and parameters: docs/CODE_INDEX.md. No HTML scripts or external report resources.
"""

import csv
import hashlib
import html
import io
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import numpy as np
from affine import Affine
from rasterio.features import shapes
from rasterio.io import MemoryFile
from rasterio.warp import transform_geom

from eostudio.engine import canonical
from eostudio.model import RESOURCES


def export_report(run: dict[str, Any], format_name: str) -> tuple[bytes, str]:
    """Render full JSON, dimensioned pixel CSV, inert HTML, actual GeoTIFF or WGS84 candidate polygons."""
    if format_name == "json":
        return canonical(run), "application/json"
    if format_name == "geojson":
        labels = np.array(run["pixels"]["region"], dtype=np.int32).reshape(
            run["grid"]["height"], run["grid"]["width"]
        )
        regions = {region["id"]: region for region in run["regions"]}
        features = []
        for geometry, identity in shapes(
            labels, mask=labels > 0, connectivity=4, transform=Affine(*run["grid"]["transform"])
        ):
            region = regions[int(identity)]
            features.append(
                {
                    "type": "Feature",
                    "geometry": transform_geom(
                        run["grid"]["crs"], "EPSG:4326", geometry, precision=7
                    ),
                    "properties": {
                        **region,
                        "report_id": run["id"],
                        "interpretation": "Unreviewed spectral candidate, not a confirmed environmental event",
                    },
                }
            )
        return canonical(
            {"type": "FeatureCollection", "features": features}
        ), "application/geo+json"
    if format_name == "tif":
        with MemoryFile() as memory:
            with memory.open(
                driver="GTiff",
                width=run["grid"]["width"],
                height=run["grid"]["height"],
                count=2,
                dtype="uint16",
                crs=run["grid"]["crs"],
                transform=Affine(*run["grid"]["transform"]),
                nodata=0,
                compress="deflate",
            ) as destination:
                for index, key in enumerate(("class", "region"), 1):
                    destination.write(
                        np.array(run["pixels"][key], dtype=np.uint16).reshape(
                            run["grid"]["height"], run["grid"]["width"]
                        ),
                        index,
                    )
                    destination.set_band_description(index, key)
                destination.update_tags(
                    author="Jason Stys",
                    report_id=run["id"],
                    meaning="0 unknown; 1 below threshold; 2 increase; 3 decrease; 4 filtered candidate. Region 0 means no retained region.",
                )
            return memory.read(), "image/tiff"
    if format_name == "csv":
        buffer = io.StringIO(newline="")
        keys = [
            "row",
            "column",
            "easting_m",
            "northing_m",
            "before_index",
            "after_index",
            "delta",
            "class",
            "region",
        ]
        writer = csv.DictWriter(buffer, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        a, _, c, _, e, f = run["grid"]["transform"]
        for index in range(run["summary"]["pixels"]):
            row, column = divmod(index, run["grid"]["width"])
            writer.writerow(
                {
                    "row": row,
                    "column": column,
                    "easting_m": c + (column + 0.5) * a,
                    "northing_m": f + (row + 0.5) * e,
                    **{key: run["pixels"][key][index] for key in keys[4:]},
                }
            )
        return buffer.getvalue().encode(), "text/csv"
    if format_name != "html":
        raise ValueError("Unsupported report format")
    escaped = html.escape(canonical(run).decode())
    page = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Environmental Change Evidence by Jason Stys</title><h1>Earth Observation Change Studio</h1><p>By Jason Stys. Spectral candidates require human review; not confirmed events or operational surveillance.</p><p>Complete source identities, grids, exclusions, thresholds, candidate regions and limitations follow.</p><pre>'
        + escaped
        + "</pre></html>"
    )
    return page.encode(), "text/html"


def save_history(path: Path, run: dict[str, Any]) -> None:
    """Verify full report identity, insert idempotently, and refuse pruning/updates after 100 reports."""
    content = dict(run)
    identity = content.pop("id", None)
    if not isinstance(identity, str) or hashlib.sha256(canonical(content)).hexdigest() != identity:
        raise ValueError("Report hash mismatch")
    schema = (RESOURCES / "history.sql").read_text(encoding="utf-8")
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(schema)
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT 1 FROM runs WHERE id=?", (identity,)).fetchone():
            return
        if connection.execute("SELECT count(*) FROM runs").fetchone()[0] >= 100:
            raise ValueError("History full; choose a new local history path")
        connection.execute(
            "INSERT INTO runs(id,scenario,report_json) VALUES(?,?,?)",
            (identity, run["name"], canonical(run).decode()),
        )

"""Hostile data/schema and genuine geospatial export contracts by Jason Stys.

Functions create task-owned synthetic rasters and exercise strict scene/manifest/export boundaries.
Variables/definitions: docs/CODE_INDEX.md. No tests fetch remote data or use private imagery.
"""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine
from rasterio.io import MemoryFile

from eostudio.engine import build_run, canonical, catalog, run_id
from eostudio.model import CHOICES, Settings, fixture, load_pair
from eostudio.raster import Grid, read_scene
from eostudio.reports import export_report


def write_scene(path, *, shape=(4, 4), count=5, dtype="float32", crs="EPSG:32610", data=None):
    """Create bounded synthetic GTiffs, never external or executable file fixtures."""
    if data is None:
        data = np.full((count, *shape), 0.3, dtype=dtype)
        if count == 5:
            data[4] = 4
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=shape[1],
        height=shape[0],
        count=count,
        dtype=dtype,
        crs=crs,
        transform=Affine(10, 0, 700000, 0, -10, 4000000),
        nodata=-9999 if dtype == "float32" else 0,
    ) as dst:
        dst.write(data)


def manifest(tmp_path):
    """Create a genuine two-raster manifest with fresh exact bytes/hashes and chronological UTC dates."""
    result = {"schema": 1, "name": "custom", "attribution": "Synthetic local test"}
    for index, key in enumerate(("before", "after"), 1):
        path = tmp_path / f"{key}.tif"
        write_scene(path)
        result[key] = {
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "datetime": f"2020-04-0{index}T00:00:00Z",
        }
    path = tmp_path / "input.json"
    path.write_text(json.dumps(result), encoding="utf-8")
    return path, result


@pytest.mark.parametrize("key", CHOICES)
@pytest.mark.parametrize("value", [None, True, 99, 1.0, [], {}, "not-supported"])
def test_control_types_and_enums(key, value):
    """All finite selectors reject unsupported values and implicit bool/number/string coercions."""
    with pytest.raises(ValueError):
        Settings(**{key: value})


@pytest.mark.parametrize("value", [None, True, 1, "unknown", [], {}])
def test_unknown_case(value):
    """Reject unknown built-in scenarios before any source file or numerical work."""
    with pytest.raises(ValueError):
        Settings(scenario=value)
    with pytest.raises((ValueError, TypeError)):
        fixture(value)


@pytest.mark.parametrize(
    "change",
    [
        {"width": 0},
        {"width": True},
        {"height": 129},
        {"height": 1.0},
        {"crs": "EPSG:4326"},
        {"crs": "EPSG:32661"},
        {"crs": None},
        {"transform": (10, 0, 0, 0, -10, 4000000)},
        {"transform": (10, 1, 700000, 0, -10, 4000000)},
        {"transform": (0, 0, 700000, 0, -10, 4000000)},
        {"transform": (10, 0, 700000, 0, 10, 4000000)},
        {"transform": (10, 0, 700000, 0, -10, -1)},
        {"transform": (float("nan"), 0, 700000, 0, -10, 4000000)},
        {"transform": (10**1000, 0, 700000, 0, -10, 4000000)},
        {"transform": (1, 2, 3)},
        {"transform": ("10", 0, 700000, 0, -10, 4000000)},
    ],
)
def test_grid_limits(change):
    """Grid bounds reject unsupported CRSs, oversized arrays, rotations and non-finite quantities."""
    with pytest.raises(ValueError):
        replace(fixture("no-change").before.grid, **change)


def test_scene_types_and_invalid_reflectance():
    """Array shape, dtype, SCL and valid-pixel radiometry are separate checked contracts."""
    scene = fixture("no-change").before
    for change in (
        {"bands": scene.bands[:, :2]},
        {"bands": scene.bands.astype(np.float32)},
        {"valid": scene.valid.astype(np.uint8)},
        {"scl": np.full_like(scene.scl, 12)},
        {"bands": scene.bands * 10},
    ):
        with pytest.raises(ValueError):
            replace(scene, **change)
    assert (
        Grid(1, 1, "EPSG:32760", (10, 0, 700000, 0, -10, 4000000)).document()["pixel_area_m2"]
        == 100
    )


@pytest.mark.parametrize(
    "change", [{"count": 4}, {"dtype": "uint16"}, {"crs": None}, {"shape": (129, 4)}]
)
def test_raster_header_contracts(tmp_path, change):
    """Reject unsupported band counts, encodings, missing CRS and excessive decoded dimensions."""
    path = tmp_path / "bad.tif"
    write_scene(path, **change)
    with pytest.raises(ValueError):
        read_scene(path)


def test_raster_nodata_invalid_scl_and_size(tmp_path, monkeypatch):
    """Nodata and invalid reflectance remain excluded; malformed SCL and file envelopes fail."""
    path = tmp_path / "valid.tif"
    data = np.full((5, 4, 4), 0.3, dtype=np.float32)
    data[4] = 4
    data[0, 0, 0] = -9999
    data[1, 1, 1] = float("inf")
    write_scene(path, data=data)
    scene = read_scene(path)
    assert scene.valid.sum() == 14
    data[4, 2, 2] = 4.5
    write_scene(path, data=data)
    with pytest.raises(ValueError, match="SCL"):
        read_scene(path)
    for value in (-1, 12):
        data[4, 2, 2] = value
        write_scene(path, data=data)
        with pytest.raises(ValueError):
            read_scene(path)
    empty = tmp_path / "empty.tif"
    empty.touch()
    with pytest.raises(ValueError):
        read_scene(empty)
    huge = tmp_path / "huge.tif"
    with huge.open("wb") as stream:
        stream.truncate(16_777_217)
    with pytest.raises(ValueError):
        read_scene(huge)
    with pytest.raises(ValueError):
        read_scene(tmp_path / "data.vrt")
    monkeypatch.setattr(Path, "is_symlink", lambda self: True)
    with pytest.raises(ValueError):
        read_scene(path)


@pytest.mark.parametrize(
    "mutation",
    [
        "root-list",
        "schema-bool",
        "name",
        "attribution",
        "extra",
        "scene-list",
        "scene-extra",
        "path",
        "hash",
        "date",
        "chronology",
        "checksum",
    ],
)
def test_manifest_mutations(tmp_path, mutation):
    """Every local manifest shape/path/date/identity boundary rejects rather than silently coercing."""
    path, doc = manifest(tmp_path)
    if mutation == "root-list":
        doc = []
    elif mutation == "schema-bool":
        doc["schema"] = True
    elif mutation == "name":
        doc["name"] = "../escape"
    elif mutation == "attribution":
        doc["attribution"] = ""
    elif mutation == "extra":
        doc["url"] = "https://example.invalid/"
    elif mutation == "scene-list":
        doc["before"] = []
    elif mutation == "scene-extra":
        doc["before"]["more"] = 1
    elif mutation == "path":
        doc["before"]["file"] = "../outside.tif"
    elif mutation == "hash":
        doc["before"]["sha256"] = "x"
    elif mutation == "date":
        doc["before"]["datetime"] = "2020-99-01T00:00:00Z"
    elif mutation == "chronology":
        doc["after"]["datetime"] = doc["before"]["datetime"]
    else:
        doc["before"]["sha256"] = "0" * 64
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError):
        load_pair(path)


@pytest.mark.parametrize(
    "body", [b"x" * 8193, b"{}", b"[]", b'{"schema":1,"schema":1}', b"\xff", b"[" * 3000]
)
def test_manifest_envelopes(tmp_path, body):
    """Reject duplicate keys, invalid UTF-8, bad nesting and oversized manifests with controlled errors."""
    path = tmp_path / "data.json"
    path.write_bytes(body)
    with pytest.raises(ValueError):
        load_pair(path)


def test_real_manifest_and_all_exports(tmp_path):
    """Exercise genuine GeoTIFF, WGS84 polygon, row CSV and escaped HTML roundtrips."""
    path, _ = manifest(tmp_path)
    custom = load_pair(path)
    assert custom.name == "custom" and custom.before.grid.width == 4
    report = build_run(Settings("vegetation-loss"))
    assert json.loads(export_report(report, "json")[0])["id"] == run_id(report)
    body, content_type = export_report(report, "tif")
    assert content_type == "image/tiff"
    with MemoryFile(body) as memory, memory.open() as src:
        assert src.count == 2 and src.crs.to_epsg() == 32610
        assert src.tags()["report_id"] == report["id"]
        assert int((src.read(1) == 3).sum()) == 192
        assert int((src.read(2) == 1).sum()) == 192
    features = json.loads(export_report(report, "geojson")[0])["features"]
    assert len(features) == 1 and features[0]["properties"]["pixels"] == 192
    lon, lat = features[0]["geometry"]["coordinates"][0][0]
    assert -123 < lon < -119 and 35 < lat < 38
    csv = export_report(report, "csv")[0].decode()
    assert len(csv.splitlines()) == 1025 and "easting_m" in csv
    report["name"] = "<img src=x onerror=alert(1)>"
    html = export_report(report, "html")[0].decode()
    assert "&lt;img" in html and "<img" not in html and "<script" not in html
    assert b"NaN" not in canonical(report)
    with pytest.raises(ValueError):
        export_report(report, "unsupported")
    assert catalog()["defaults"]["metric"] == "ndvi"


@pytest.mark.parametrize("value", [None, 42, "2020-04-01", "2020-04-01T00:00:00+01:00"])
def test_explicit_utc_timestamp_format(tmp_path, value):
    """Reject missing/non-UTC timestamp contracts before chronological comparison."""
    path, doc = manifest(tmp_path)
    doc["before"]["datetime"] = value
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError, match="UTC"):
        load_pair(path)

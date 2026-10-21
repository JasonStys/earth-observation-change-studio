"""Independent analytical, metamorphic and full-selector acceptance by Jason Stys.

Functions test known rectangles, masks, alignment, connected components and scalar/vector gates.
Variables and definition lines: docs/CODE_INDEX.md. Synthetic truth is never an observed-event label.
"""

from dataclasses import replace
from itertools import product

import numpy as np
import pytest
from hypothesis import given
from hypothesis import settings as campaigns
from hypothesis import strategies as st

from eostudio import engine
from eostudio.engine import analyze, build_run, components, expand_invalid, indices, run_id
from eostudio.model import CASES, CHOICES, Pair, Settings, fixture
from eostudio.raster import Grid, Scene, align


@pytest.mark.parametrize("values", list(product(CASES, *CHOICES.values())))
def test_all_controls(values):
    """Exercise all 864 combinations against the independent scalar model and accounting gates."""
    report = build_run(Settings(*values))
    assert report["id"] == run_id(report)
    assert sum(report["quality"].values()) == report["summary"]["pixels"]
    assert report["summary"]["candidate_pixels"] == sum(r["pixels"] for r in report["regions"])
    assert report["method"]["reference_verified"] is True
    assert report["summary"]["candidate_ha"] >= 0
    assert report["truth"] is None if values[0] == "central-valley" else report["truth"] is not None


def test_hand_derived_rectangle_and_area():
    """A 12x16 rectangle has 192 changed pixels, one region and 1.92 nominal hectares at 10m."""
    report = build_run(Settings("vegetation-loss"))
    assert report["summary"]["candidate_pixels"] == 192
    assert report["summary"]["candidate_ha"] == 1.92
    assert report["summary"]["decrease_pixels"] == 192
    assert report["regions"][0]["bbox_rc"] == [8, 6, 20, 22]
    assert report["truth"]["iou"] == 1
    assert report["truth"]["recall"] == report["truth"]["precision"] == 1
    assert report["summary"]["comparable"] == 30 * 30


def test_water_index_direction_and_nulls():
    """Water-like spectra increase green/NIR NDWI while NDVI falls; all-masked results are not zero rates."""
    water = build_run(Settings("water-gain", metric="ndwi"))
    assert water["summary"]["increase_pixels"] == 192
    for case in ("all-masked", "denominator-zero"):
        report = build_run(Settings(case))
        assert report["summary"]["comparable"] == 0
        assert report["summary"]["candidate_fraction"] is None
        assert report["summary"]["mean_delta"] is None
        assert report["truth"]["precision"] is None
        assert set(report["pixels"]["class"]) == {0}
    assert build_run(Settings("cloud-trap"))["summary"]["candidate_pixels"] == 0


def test_nearest_alignment_translation():
    """Analytic pixel-centre translation, not the warp helper, supplies expected shifted samples."""
    pair = fixture("shifted-grid")
    data = pair.after.bands.copy()
    for column in range(32):
        data[:, :, column] = column / 100
    shifted = align(replace(pair.after, bands=data), pair.before.grid)
    assert not shifted.valid[:, :2].any()
    assert shifted.valid[:, 2:].all()
    for column in range(2, 32):
        assert np.all(shifted.bands[:, :, column] == (column - 2) / 100)
    assert align(pair.before, pair.before.grid) is pair.before
    assert build_run(Settings("shifted-grid"))["summary"]["candidate_pixels"] == 0


def test_components_no_diagonal_or_opposite_sign_merging():
    """Four-connectivity and same-sign membership prevent diagonal/opposite candidates merging."""
    raw = np.array([[2, 3, 1], [1, 2, 1], [2, 2, 0]], dtype=np.uint8)
    final, labels, regions = components(raw, 2)
    assert len(regions) == 1 and regions[0]["pixels"] == 3
    assert final[0, 0] == final[0, 1] == 4
    assert labels[0, 0] == labels[0, 1] == 0
    assert labels[1, 1] == labels[2, 0] == labels[2, 1] == 1
    assert components(np.ones((2, 2), dtype=np.uint8), 1)[2] == []


def test_quality_policy_denominator_and_margin():
    """Quality stage counts are disjoint; class 7 is opt-in, crop-edge margins are conservative."""
    pair = fixture("no-change")
    scl = pair.after.scl.copy()
    scl[10, 10] = 7
    bands = pair.after.bands.copy()
    bands[:, 12, 12] = 0
    valid = pair.after.valid.copy()
    valid[14, 14] = False
    pair = replace(pair, after=replace(pair.after, scl=scl, bands=bands, valid=valid))
    strict = analyze(pair, Settings("no-change", margin=0))
    loose = analyze(pair, Settings("no-change", margin=0, quality="unclassified"))
    assert strict["quality"]["scl_excluded"] == 1
    assert strict["quality"]["denominator_excluded"] == 1
    assert strict["quality"]["data_excluded"] == 1
    assert loose["quality"]["comparable"] == strict["quality"]["comparable"] + 1
    mask = np.zeros((5, 5), dtype=np.bool_)
    mask[2, 2] = True
    assert expand_invalid(mask, 0).sum() == 1
    assert expand_invalid(mask, 1).all()


def test_unrounded_classification_and_sensitivity():
    """Thresholds are inclusive on unrounded ratios; sensitivity counts must be monotonic."""
    pair = fixture("no-change")
    before = replace(pair.before, bands=np.full_like(pair.before.bands, 0.5))
    data = before.bands.copy()
    data[3], data[0] = 0.75, 0.25
    after = replace(pair.after, bands=data)
    report = analyze(
        replace(pair, before=before, after=after), Settings("no-change", threshold=30, margin=0)
    )
    assert report["summary"]["increase_pixels"] == 1024
    assert report["truth"]["fp"] == 1024 and report["truth"]["precision"] == 0
    counts = [row["raw_candidate_pixels"] for row in report["sensitivity"]]
    assert counts == sorted(counts, reverse=True)
    assert report["pixels"]["delta"][0] == 0.5


def test_disagreement_and_accounting_fail_closed(monkeypatch):
    """Injected oracle or component discrepancies withhold evidence instead of returning success."""
    original = engine.evaluate

    def wrong(*args):
        """Corrupt an independent class decision to exercise the differential gate."""
        a, b, classes = original(*args)
        classes[0] = 2
        return a, b, classes

    monkeypatch.setattr(engine, "evaluate", wrong)
    with pytest.raises(RuntimeError, match="scalar/vector"):
        build_run(Settings("no-change"))
    monkeypatch.setattr(engine, "evaluate", original)
    component = engine.components

    def broken(*args):
        """Drop region metadata while retaining changed pixels to break conservation accounting."""
        final, labels, _ = component(*args)
        return final, labels, []

    monkeypatch.setattr(engine, "components", broken)
    with pytest.raises(RuntimeError, match="accounting"):
        build_run(Settings("vegetation-loss"))


@campaigns(max_examples=100, deadline=None)
@given(
    st.lists(
        st.floats(min_value=0, max_value=1.5, allow_nan=False, allow_infinity=False),
        min_size=16,
        max_size=16,
    )
)
def test_generated_spectral_profiles(values):
    """One hundred small bounded spectra exercise independent ratios, masks and finite reports."""
    grid = Grid(2, 2, "EPSG:32610", (10, 0, 700000, 0, -10, 4000000))
    bands = np.array(values, dtype=np.float64).reshape(4, 2, 2)
    scene = Scene(grid, bands, np.full((2, 2), 4, dtype=np.uint8), np.ones((2, 2), dtype=np.bool_))
    pair = Pair("generated", scene, scene, {"kind": "synthetic"})
    report = analyze(pair, Settings("no-change", margin=0, minimum=1))
    assert report["summary"]["candidate_pixels"] == 0
    assert report["id"] == run_id(report)
    assert np.isfinite(indices(scene, "ndvi")[scene.valid & ((bands[3] + bands[0]) > 1e-6)]).all()

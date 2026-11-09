"""Independent local raster-neighborhood counts by Jason Stys.

Functions: test_*; variables: hand-written class/region matrices, unknown fringe and crop boundaries.
No context flag is an environmental diagnosis. Exact lines: docs/CODE_INDEX.md.
"""

import json

import numpy as np
import pytest

from eostudio.context import region_context
from eostudio.engine import build_run
from eostudio.model import Settings
from eostudio.reports import export_report


def test_unknown_four_neighbor_ring_and_diagonal_exclusion():
    """A center cell has four immediate neighbors; diagonal unknowns are outside this defined ring."""
    labels = np.zeros((3, 3), dtype=np.int32)
    labels[1, 1] = 1
    classes = np.ones((3, 3), dtype=np.uint8)
    classes[1, 1] = 2
    classes[0, 0] = 0
    regions = [{"id": 1}]
    region_context(labels, classes, regions)
    assert regions[0]["context"]["complete_four_neighbor_context"]
    classes[0, 1] = 0
    region_context(labels, classes, regions)
    context = regions[0]["context"]
    assert context["neighbor_pixels"] == 4 and context["excluded_neighbors"] == 1
    assert context["unchanged_neighbors"] == 3 and not context["complete_four_neighbor_context"]
    json.dumps(context)


def test_crop_edges_and_unique_neighbor_counts():
    """The missing interior of an L touches two cells but counts once; crop edges stay separate."""
    labels = np.array([[1, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=np.int32)
    classes = np.where(labels > 0, 2, 1).astype(np.uint8)
    classes[1, 1] = 0
    classes[0, 2] = 4
    classes[2, 0] = 3
    regions = [{"id": 1}]
    region_context(labels, classes, regions)
    context = regions[0]["context"]
    assert context["neighbor_pixels"] == 3 and context["crop_edge_sides"] == 4
    assert (
        context["excluded_neighbors"]
        == context["filtered_candidate_neighbors"]
        == context["other_candidate_neighbors"]
        == 1
    )
    assert context["touches_crop_edge"]
    region_context(np.zeros((2, 2), dtype=np.int32), np.ones((2, 2), dtype=np.uint8), [])
    with pytest.raises(RuntimeError, match="accounting"):
        region_context(labels, classes, [])


def test_region_exports_keep_context_without_changing_candidate_classification():
    """Full JSON and geographic candidate properties carry the same report-bound review context."""
    run = build_run(Settings(scenario="vegetation-loss", margin=0))
    assert run["regions"]
    geo = json.loads(export_report(run, "geojson")[0])
    assert geo["features"][0]["properties"]["context"] == run["regions"][0]["context"]
    for region in run["regions"]:
        context = region["context"]
        assert context["neighbor_pixels"] == sum(
            context[key]
            for key in (
                "excluded_neighbors",
                "unchanged_neighbors",
                "filtered_candidate_neighbors",
                "other_candidate_neighbors",
            )
        )

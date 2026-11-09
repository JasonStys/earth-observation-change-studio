"""Candidate-region four-neighbor context by Jason Stys.

Function: region_context. Variables: region-local unique fringe pixels and crop-edge interfaces.
Unknown context remains excluded, never unchanged or a confirmed environmental label.
Exact definitions/variable lines: docs/CODE_INDEX.md.
"""

from typing import Any

import numpy as np
from numpy.typing import NDArray


def region_context(
    labels: NDArray[np.int32], classes: NDArray[np.uint8], regions: list[dict[str, Any]]
) -> None:
    """Annotate retained regions in O(pixels), counting distinct four-neighbor fringe pixels.

    Counts are per region: one surrounding pixel can neighbor more than one region, so these
    counts must not be summed as a disjoint scene-quality total. Crop-edge sides are separate.
    """
    height, width = labels.shape
    fringe: dict[int, set[tuple[int, int]]] = {region["id"]: set() for region in regions}
    edges = dict.fromkeys(fringe, 0)
    for y in range(height):
        for x in range(width):
            identity = int(labels[y, x])
            if identity == 0:
                continue
            if identity not in fringe:
                raise RuntimeError("Region context accounting mismatch")
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if not (0 <= ny < height and 0 <= nx < width):
                    edges[identity] += 1
                elif labels[ny, nx] != identity:
                    fringe[identity].add((ny, nx))
    for region in regions:
        identity = region["id"]
        counts = {
            code: sum(classes[y, x] == code for y, x in fringe[identity]) for code in range(5)
        }
        region["context"] = {
            "neighbor_pixels": len(fringe[identity]),
            "excluded_neighbors": int(counts[0]),
            "unchanged_neighbors": int(counts[1]),
            "other_candidate_neighbors": int(counts[2] + counts[3]),
            "filtered_candidate_neighbors": int(counts[4]),
            "crop_edge_sides": edges[identity],
            "touches_crop_edge": edges[identity] > 0,
            "complete_four_neighbor_context": bool(edges[identity] == 0 and counts[0] == 0),
        }

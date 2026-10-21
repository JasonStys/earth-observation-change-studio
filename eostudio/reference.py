"""Scalar independent spectral/quality oracle by Jason Stys; not an accuracy claim about satellites.

Function: evaluate. Variables: allowed SCL, individual ratios, comparison eligibility and margin loops.
Exact definition/variable lines: docs/CODE_INDEX.md. No vectorized production helper is called here.
"""

from eostudio.model import Settings
from eostudio.raster import Scene


def evaluate(
    before: Scene, after: Scene, settings: Settings
) -> tuple[list[float | None], list[float | None], list[int]]:
    """Independently derive ratios and raw change classes, including conservative square quality margins."""
    height, width = before.grid.height, before.grid.width
    allowed = {4, 5, 6} if settings.quality == "strict" else {4, 5, 6, 7}
    first: list[float | None] = []
    second: list[float | None] = []
    eligible: list[bool] = []
    for row in range(height):
        for column in range(width):
            indices: list[float | None] = []
            quality = True
            for scene in (before, after):
                quality = (
                    quality
                    and bool(scene.valid[row, column])
                    and int(scene.scl[row, column]) in allowed
                )
                upper = float(scene.bands[3 if settings.metric == "ndvi" else 1, row, column])
                lower = float(scene.bands[0 if settings.metric == "ndvi" else 3, row, column])
                indices.append(
                    (upper - lower) / (upper + lower)
                    if bool(scene.valid[row, column]) and upper + lower > 1e-6
                    else None
                )
            first.append(indices[0])
            second.append(indices[1])
            eligible.append(quality and indices[0] is not None and indices[1] is not None)
    classes = []
    for row in range(height):
        for column in range(width):
            index = row * width + column
            valid = True
            for dr in range(-settings.margin, settings.margin + 1):
                for dc in range(-settings.margin, settings.margin + 1):
                    y, x = row + dr, column + dc
                    if not (0 <= y < height and 0 <= x < width) or not eligible[y * width + x]:
                        valid = False
            a, b = first[index], second[index]
            difference = b - a if a is not None and b is not None else 0
            classes.append(
                0
                if not valid
                else 2
                if difference >= settings.threshold / 100
                else 3
                if difference <= -settings.threshold / 100
                else 1
            )
    return first, second, classes

"""Vectorized spectral candidates, connected regions and traceable evidence by Jason Stys.

Functions: build_run, analyze, indices, components, canonical, run_id. Variables: fixed class codes/method limits.
All definition and variable locations: docs/CODE_INDEX.md. Candidates are not confirmed environmental events.
"""

import hashlib
import json
import math
from collections import deque
from dataclasses import asdict
from typing import Any

import numpy as np
from numpy.typing import NDArray

from eostudio.model import CASES, CHOICES, Pair, Settings, fixture
from eostudio.raster import FloatGrid, Scene, align
from eostudio.reference import evaluate

LIMITS = [
    "Spectral candidates are not confirmed flood, damage or vegetation-loss labels; seasonal/illumination/atmospheric effects can explain differences.",
    "Native SCL and nearest-neighbour alignment do not guarantee cloud removal, subpixel registration or sensor calibration.",
    "A fixed threshold and minimum region size are heuristics, not learned probabilities; threshold sensitivity is not statistical confidence.",
    "Pixel areas are nominal UTM grid areas, not geodesic survey measurements. One small crop and two dates cannot establish event cause.",
    "Synthetic truth is only a software oracle. Public crops have no independent ground truth or accuracy score.",
]


def canonical(value: Any) -> bytes:
    """Serialize complete finite ASCII evidence without hidden host paths, timestamps or secrets."""
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    ).encode()


def run_id(run: dict[str, Any]) -> str:
    """Hash the complete quantized evidence excluding its own identity; hashes are not signatures."""
    return hashlib.sha256(
        canonical({key: value for key, value in run.items() if key != "id"})
    ).hexdigest()


def catalog() -> dict[str, Any]:
    """Publish only finite built-in selectors, never local paths, network addresses or executables."""
    return {"scenarios": CASES, "choices": CHOICES, "defaults": asdict(Settings())}


def indices(scene: Scene, metric: str) -> FloatGrid:
    """Calculate NDVI or green/NIR NDWI without zero-denominator or invalid-reflectance coercion."""
    a, b = (
        (scene.bands[3], scene.bands[0]) if metric == "ndvi" else (scene.bands[1], scene.bands[3])
    )
    a, b = np.where(scene.valid, a, 0), np.where(scene.valid, b, 0)
    output = np.full(a.shape, np.nan, dtype=np.float64)
    np.divide(a - b, a + b, out=output, where=scene.valid & (a + b > 1e-6))
    return output


def expand_invalid(mask: NDArray[np.bool_], margin: int) -> NDArray[np.bool_]:
    """Dilate invalid comparison pixels by a square radius; outside the crop is unknown, not clear."""
    height, width = mask.shape
    padded = np.pad(mask, margin, constant_values=True)
    result = np.zeros_like(mask)
    for row in range(2 * margin + 1):
        for column in range(2 * margin + 1):
            result |= padded[row : row + height, column : column + width]
    return result


def components(
    raw: NDArray[np.uint8], minimum: int
) -> tuple[NDArray[np.uint8], NDArray[np.int32], list[dict[str, Any]]]:
    """Four-connect same-sign candidate cells in O(N), retaining region IDs in row-major discovery order."""
    height, width = raw.shape
    visited = np.zeros(raw.shape, dtype=np.bool_)
    labels = np.zeros(raw.shape, dtype=np.int32)
    final = raw.copy()
    regions: list[dict[str, Any]] = []
    for row in range(height):
        for column in range(width):
            sign = int(raw[row, column])
            if sign not in (2, 3) or visited[row, column]:
                continue
            pending = deque([(row, column)])
            visited[row, column] = True
            cells = []
            while pending:
                y, x = pending.popleft()
                cells.append((y, x))
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and not visited[ny, nx]
                        and raw[ny, nx] == sign
                    ):
                        visited[ny, nx] = True
                        pending.append((ny, nx))
            if len(cells) < minimum:
                for y, x in cells:
                    final[y, x] = 4
                continue
            identity = len(regions) + 1
            for y, x in cells:
                labels[y, x] = identity
            regions.append(
                {
                    "id": identity,
                    "direction": "increase" if sign == 2 else "decrease",
                    "pixels": len(cells),
                    "bbox_rc": [
                        min(y for y, _ in cells),
                        min(x for _, x in cells),
                        max(y for y, _ in cells) + 1,
                        max(x for _, x in cells) + 1,
                    ],
                    "review": "unreviewed",
                }
            )
    return final, labels, regions


def nullable(array: FloatGrid) -> list[float | None]:
    """Quantize only report values; missing indices remain null and classifications use unrounded data."""
    return [round(float(v), 6) if math.isfinite(float(v)) else None for v in array.ravel()]


def rgb(scene: Scene) -> list[int]:
    """Use one fixed 0..0.35 linear display stretch for both dates; analysis retains physical values."""
    colors = (
        np.clip(np.nan_to_num(scene.bands[:3], nan=0, posinf=0, neginf=0), 0, 0.35) / 0.35 * 255
    )
    color = colors.astype(np.uint32)
    return ((color[0] << 16) | (color[1] << 8) | color[2]).ravel().tolist()  # type: ignore[no-any-return]


def analyze(pair: Pair, settings: Settings) -> dict[str, Any]:
    """Require scalar/vector agreement, explicit exclusion accounting and synthetic-only truth metrics."""
    before, after = pair.before, align(pair.after, pair.before.grid)
    a, b = indices(before, settings.metric), indices(after, settings.metric)
    footprint = before.valid & after.valid
    allowed = (4, 5, 6) if settings.quality == "strict" else (4, 5, 6, 7)
    qa = footprint & np.isin(before.scl, allowed) & np.isin(after.scl, allowed)
    denominator = qa & np.isfinite(a) & np.isfinite(b)
    valid = ~expand_invalid(~denominator, settings.margin)
    delta = b - a
    threshold = settings.threshold / 100
    raw = np.where(
        ~valid, 0, np.where(delta >= threshold, 2, np.where(delta <= -threshold, 3, 1))
    ).astype(np.uint8)
    ra, rb, reference = evaluate(before, after, settings)
    if not np.array_equal(raw.ravel(), reference) or any(
        (math.isfinite(float(value)) != (expected is not None))
        or (
            expected is not None
            and not math.isclose(float(value), expected, rel_tol=1e-12, abs_tol=1e-12)
        )
        for actual, expected_values in ((a, ra), (b, rb))
        for value, expected in zip(actual.ravel(), expected_values, strict=True)
    ):
        raise RuntimeError("Independent scalar/vector check failed; evidence withheld")
    final, labels, regions = components(raw, settings.minimum)
    count = int(valid.sum())
    total = final.size
    retained = (final == 2) | (final == 3)
    retained_count = int(retained.sum())
    quality = {
        "data_excluded": int(total - footprint.sum()),
        "scl_excluded": int(footprint.sum() - qa.sum()),
        "denominator_excluded": int(qa.sum() - denominator.sum()),
        "margin_excluded": int(denominator.sum() - valid.sum()),
        "comparable": count,
    }
    if sum(quality.values()) != total or retained_count != sum(
        region["pixels"] for region in regions
    ):
        raise RuntimeError("Pixel accounting failed; evidence withheld")
    grid = before.grid.document()
    area = grid["pixel_area_m2"] / 10000
    truth = None
    if pair.truth is not None:
        tp = int((retained & pair.truth & valid).sum())
        fp = int((retained & ~pair.truth & valid).sum())
        fn = int((~retained & pair.truth & valid).sum())
        truth = {
            "domain": "Comparable synthetic pixels only, not public-image accuracy",
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "evaluated": count,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "iou": tp / (tp + fp + fn) if tp + fp + fn else None,
        }
    report: dict[str, Any] = {
        "schema": 1,
        "name": pair.name,
        "settings": asdict(settings),
        "grid": grid,
        "provenance": pair.provenance,
        "method": {
            "author": "Jason Stys",
            "version": "spectral-v1",
            "alignment": "after to before grid, nearest neighbour; no feature-based registration",
            "index": "(NIR-red)/(NIR+red)"
            if settings.metric == "ndvi"
            else "(green-NIR)/(green+NIR)",
            "denominator_min": 1e-6,
            "reference_verified": True,
            "connectivity": 4,
            "threshold": threshold,
            "quality_margin": "Chebyshev radius in target pixels, includes unknown crop edges",
            "rgb_display": "Same linear reflectance 0..0.35 stretch; clipping is display-only",
        },
        "limits": LIMITS,
        "summary": {
            "pixels": total,
            "comparable": count,
            "comparable_fraction": count / total,
            "candidate_pixels": retained_count,
            "candidate_fraction": retained_count / count if count else None,
            "candidate_ha": round(retained_count * area, 6),
            "increase_pixels": int((final == 2).sum()),
            "decrease_pixels": int((final == 3).sum()),
            "filtered_pixels": int((final == 4).sum()),
            "regions": len(regions),
            "mean_delta": round(float(delta[valid].mean()), 6) if count else None,
        },
        "quality": quality,
        "truth": truth,
        "sensitivity": [
            {
                "threshold": round(t, 2),
                "raw_candidate_pixels": int((valid & (np.abs(delta) >= t)).sum()),
            }
            for t in (threshold - 0.05, threshold, threshold + 0.05)
        ],
        "regions": regions,
        "pixels": {
            "before_index": nullable(a),
            "after_index": nullable(b),
            "delta": nullable(np.where(valid, delta, np.nan)),
            "class": final.ravel().tolist(),
            "region": labels.ravel().tolist(),
            "before_rgb": rgb(before),
            "after_rgb": rgb(after),
        },
    }
    report["id"] = run_id(report)
    return report


def build_run(settings: Settings | None = None) -> dict[str, Any]:
    """Analyze one fresh fixed fixture; no global scene mutation, network request or data upload."""
    settings = settings or Settings()
    return analyze(fixture(settings.scenario), settings)

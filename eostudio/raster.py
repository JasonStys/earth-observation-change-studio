"""Bounded local GeoTIFF contracts and nearest-grid alignment by Jason Stys.

Types: Grid, Scene. Functions validate local arrays, read exact GTiff bands and align to the first grid.
Variables/fields and line locations: docs/CODE_INDEX.md. Runtime never opens a remote raster URL.
"""

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from affine import Affine
from numpy.typing import NDArray
from rasterio.enums import Resampling
from rasterio.warp import reproject

FloatGrid = NDArray[np.float64]
BoolGrid = NDArray[np.bool_]


@dataclass(frozen=True)
class Grid:
    """North-up UTM metre grid, at most 128² cells; nominal areas are projected, not geodesic."""

    width: int
    height: int
    crs: str
    transform: tuple[float, ...]

    def __post_init__(self) -> None:
        """Reject unsafe dimensions, unknown CRS, rotations, nonfinite values and invalid UTM extent."""
        if any(type(v) is not int or not 1 <= v <= 128 for v in (self.width, self.height)):
            raise ValueError("Raster dimensions must be 1..128")
        if not isinstance(self.crs, str) or not re.fullmatch(
            r"EPSG:32[67](0[1-9]|[1-5][0-9]|60)", self.crs
        ):
            raise ValueError("Only WGS84 UTM metre grids are supported")
        if len(self.transform) != 6 or any(
            type(v) not in (int, float) or abs(v) > 1e8 or not math.isfinite(v)
            for v in self.transform
        ):
            raise ValueError("Invalid affine transform")
        a, b, c, d, e, f = self.transform
        if b != 0 or d != 0 or not 1 <= a <= 1000 or not -1000 <= e <= -1:
            raise ValueError("Expected north-up 1..1000 metre pixels")
        if (
            not 100000 <= c < c + a * self.width <= 900000
            or not 0 <= f + e * self.height < f <= 10000000
        ):
            raise ValueError("Grid outside supported UTM extent")

    def document(self) -> dict[str, Any]:
        """Expose finite grid coordinates and nominal pixel area without inventing geolocation accuracy."""
        return {
            "width": self.width,
            "height": self.height,
            "crs": self.crs,
            "transform": list(self.transform),
            "pixel_area_m2": abs(self.transform[0] * self.transform[4]),
        }


@dataclass(frozen=True)
class Scene:
    """Four reflectance bands (red, green, blue, NIR), SCL classes and explicit data-valid mask."""

    grid: Grid
    bands: FloatGrid
    scl: NDArray[np.uint8]
    valid: BoolGrid

    def __post_init__(self) -> None:
        """Validate complete array dimensions/types; keep invalid pixels explicit rather than zero fill."""
        shape = (self.grid.height, self.grid.width)
        if self.bands.shape != (4, *shape) or self.scl.shape != shape or self.valid.shape != shape:
            raise ValueError("Array/grid shape mismatch")
        if (
            self.bands.dtype != np.float64
            or self.scl.dtype != np.uint8
            or self.valid.dtype != np.bool_
        ):
            raise ValueError("Unexpected array types")
        if np.any(self.scl > 11) or np.any(
            self.valid
            & ~np.all(np.isfinite(self.bands) & (self.bands >= 0) & (self.bands <= 1.5), axis=0)
        ):
            raise ValueError("Invalid reflectance or classification")


def file_hash(path: Path) -> str:
    """Hash bounded local source bytes; callers validate the file before treating it as a scene."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_scene(path: Path) -> Scene:
    """Read only a bounded local five-band float32 GTiff; ignore sidecars and reject other drivers."""
    if (
        path.is_symlink()
        or path.suffix.lower() not in (".tif", ".tiff")
        or not 1 <= path.stat().st_size <= 16_777_216
    ):
        raise ValueError("Expected local GeoTIFF up to 16 MiB")
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_PAM_ENABLED="NO", GDAL_NUM_THREADS="1"
    ):
        with rasterio.open(path, driver="GTiff", sharing=False) as src:
            if src.count != 5 or set(src.dtypes) != {"float32"} or src.crs is None:
                raise ValueError("Expected red/green/blue/NIR/SCL float32 bands with a CRS")
            grid = Grid(src.width, src.height, src.crs.to_string(), tuple(src.transform)[:6])
            data = src.read().astype(np.float64)
            masks = np.all(src.read_masks() > 0, axis=0)
    classified = masks & np.isfinite(data[4])
    if np.any(classified & ((data[4] != np.floor(data[4])) | (data[4] < 0) | (data[4] > 11))):
        raise ValueError("SCL must contain integer classes 0..11")
    valid = classified & np.all(np.isfinite(data[:4]) & (data[:4] >= 0) & (data[:4] <= 1.5), axis=0)
    scl = np.where(classified, data[4], 0).astype(np.uint8)
    return Scene(grid, data[:4], scl, valid)


def align(scene: Scene, target: Grid) -> Scene:
    """Nearest-neighbour warp to the first scene grid; data coverage and SCL never use bilinear mixing."""
    if scene.grid == target:
        return scene
    bands = np.full((4, target.height, target.width), np.nan, dtype=np.float64)
    scl = np.zeros((target.height, target.width), dtype=np.uint8)
    valid = np.zeros(scl.shape, dtype=np.uint8)
    kwargs = {
        "src_transform": Affine(*scene.grid.transform),
        "src_crs": scene.grid.crs,
        "dst_transform": Affine(*target.transform),
        "dst_crs": target.crs,
        "resampling": Resampling.nearest,
        "num_threads": 1,
    }
    for index in range(4):
        reproject(
            np.where(scene.valid, scene.bands[index], np.nan),
            bands[index],
            src_nodata=np.nan,
            dst_nodata=np.nan,
            **kwargs,
        )
    reproject(scene.scl, scl, src_nodata=0, dst_nodata=0, **kwargs)
    reproject(scene.valid.astype(np.uint8), valid, src_nodata=0, dst_nodata=0, **kwargs)
    return Scene(target, bands, scl, valid.astype(np.bool_) & np.all(np.isfinite(bands), axis=0))

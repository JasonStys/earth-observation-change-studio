"""Explicit one-time public Sentinel-2 crop acquisition by Jason Stys; never run during app use.

Function: main. Variables: fixed provider IDs, bounded crop, published scale/offset and byte hashes.
Exact locations: docs/CODE_INDEX.md. Refuse new processing baselines instead of guessing radiometry.
"""

import argparse
import hashlib
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject, transform
from rasterio.windows import Window

IDS = ("S2A_10SGF_20200401_0_L2A", "S2A_10SGF_20200730_0_L2A")


def main() -> None:
    """Fetch fixed legacy-baseline COG windows with TLS intact; write a new offline dataset only."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    provenance = {
        "retrieved_utc": datetime.now(UTC).isoformat(),
        "attribution": "Contains modified Copernicus Sentinel data (2020), processed by Jason Stys; COGs supplied by Element 84",
        "method": "128x128 10m integer crop centered near -119.6,36.06; reflectance=DN*0.0001; zero offset for pinned PB02.14; native 20m SCL warped by nearest neighbour",
        "scenes": [],
    }
    manifest = {"schema": 1, "name": "central-valley", "attribution": provenance["attribution"]}
    for label, identity in zip(("before", "after"), IDS, strict=True):
        url = (
            "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/" + identity
        )
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read(262145)
        if len(raw) > 262144:
            raise ValueError("Oversized provider item")
        item = json.loads(raw)
        if (
            item["properties"]["s2:processing_baseline"] != "02.14"
            or item["properties"]["earthsearch:boa_offset_applied"] is not False
        ):
            raise ValueError("Pinned radiometric baseline changed; do not guess corrections")
        (args.output / f"{label}-stac.json").write_bytes(raw)
        bands = np.full((5, 128, 128), -9999, dtype=np.float32)
        source_records = []
        crop_transform = None
        crs = None
        with rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            GDAL_HTTP_TIMEOUT="30",
            GDAL_HTTP_MAX_RETRY="1",
            GDAL_PAM_ENABLED="NO",
        ):
            for index, band in enumerate(("red", "green", "blue", "nir")):
                asset = item["assets"][band]
                radiometry = asset["raster:bands"][0]
                if (
                    radiometry["scale"] != 0.0001
                    or radiometry["offset"] != 0
                    or radiometry["nodata"] != 0
                ):
                    raise ValueError("Unexpected legacy radiometry")
                href = asset["href"]
                if not href.startswith("https://sentinel-cogs.s3.us-west-2.amazonaws.com/"):
                    raise ValueError("Unexpected data host")
                with rasterio.open(href) as src:
                    x, y = transform("EPSG:4326", src.crs, [-119.6], [36.06])
                    row, column = src.index(x[0], y[0])
                    window = Window(column - 64, row - 64, 128, 128)
                    if (
                        window.row_off < 0
                        or window.col_off < 0
                        or window.row_off + 128 > src.height
                        or window.col_off + 128 > src.width
                    ):
                        raise ValueError("Crop must be wholly inside the source tile")
                    grid = src.window_transform(window)
                    if crop_transform is not None and (grid != crop_transform or src.crs != crs):
                        raise ValueError("Unexpected band misalignment")
                    crop_transform, crs = grid, src.crs
                    dn = src.read(1, window=window)
                    bands[index] = np.where(dn == 0, -9999, dn.astype(np.float64) * 0.0001)
                source_records.append(
                    {
                        "band": band,
                        "href": href,
                        "scale": 0.0001,
                        "offset": 0,
                        "window": [int(window.col_off), int(window.row_off), 128, 128],
                        "cropped_dn_sha256": hashlib.sha256(dn.astype("<u2").tobytes()).hexdigest(),
                    }
                )
            scl = item["assets"]["scl"]["href"]
            if not scl.startswith("https://sentinel-cogs.s3.us-west-2.amazonaws.com/"):
                raise ValueError("Unexpected SCL host")
            with rasterio.open(scl) as src:
                reproject(
                    rasterio.band(src, 1),
                    bands[4],
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=crop_transform,
                    dst_crs=crs,
                    resampling=Resampling.nearest,
                    src_nodata=0,
                    dst_nodata=-9999,
                    num_threads=1,
                )
        output = args.output / f"{label}.tif"
        with rasterio.open(
            output,
            "w",
            driver="GTiff",
            width=128,
            height=128,
            count=5,
            dtype="float32",
            crs=crs,
            transform=crop_transform,
            nodata=-9999,
            compress="deflate",
        ) as dst:
            dst.write(bands)
            for index, name in enumerate(
                (
                    "red_reflectance",
                    "green_reflectance",
                    "blue_reflectance",
                    "nir_reflectance",
                    "scl",
                ),
                1,
            ):
                dst.set_band_description(index, name)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        timestamp = item["properties"]["datetime"][:19] + "Z"
        manifest[label] = {"file": output.name, "sha256": digest, "datetime": timestamp}
        provenance["scenes"].append(
            {
                "id": identity,
                "item_url": url,
                "item_sha256": hashlib.sha256(raw).hexdigest(),
                "crop_sha256": digest,
                "scl_href": scl,
                "bands": source_records,
            }
        )
    (args.output / "central-valley.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "snapshot.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "Saved two attributed public crops and exact acquisition provenance; no operational change labels"
    )


if __name__ == "__main__":
    main()

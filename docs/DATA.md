# Public data, rights and provenance

Maintained by Jason Stys. **Contains modified Copernicus Sentinel data (2020)**, processed by Jason Stys; cloud-optimized GeoTIFFs supplied by Element 84 through its public Earth Search catalog and the Sentinel COG bucket.

## Checked-in observed sample

The pair is a 128×128-pixel, 10 m integer-window crop of agricultural land near longitude −119.6°, latitude 36.06° in California's Central Valley. It is used for civilian environmental review, not individual identification or sensitive-site monitoring. Original acquisitions are:

- `S2A_10SGF_20200401_0_L2A`, 2020-04-01.
- `S2A_10SGF_20200730_0_L2A`, 2020-07-30.

Both are pinned legacy processing baseline **02.14**, with reflectance `DN × 0.0001` and **zero radiometric offset**, as recorded by each band's retained metadata. The acquisition tool explicitly rejects changed baselines, unexpected scale/offset/nodata or unrecognized data hosts. It does not infer a correction from acquisition date alone or apply a modern offset twice. Original full STAC responses, metadata hashes, source COG URLs, cropped raw-DN hashes, crop offsets and output TIFF hashes are retained under `eostudio/resources/sentinel/`. The manifest verifies output TIFF identities at load time.

Bands B04 red, B03 green, B02 blue and B08 NIR are cropped and converted to float32 normalized reflectance. The native 20 m SCL raster is nearest-warped to the 10 m crop without mixing classes. Zero source digital numbers remain nodata; no missing data is fabricated. Original source COG files are not redistributed whole, and a cropped-DN hash is not falsely described as the hash of the complete remote object. No independent environmental-change labels accompany these observations.

The exact centre is rounded to source integer pixels; the stored TIFF transforms, not the approximate requested longitude/latitude, define actual pixel centres and boundaries. A source tile intersecting a search bounding box does not necessarily contain its centre. Development caught that distinction; the acquisition tool now rejects any crop not wholly inside the source raster.

## Reproduce acquisition explicitly

The application, tests and release workflow need no network data access. To make a **new** dataset directory manually:

```powershell
.venv/Scripts/python tools/acquire_sample.py --output new-public-crop
```

The script refuses an existing output directory. Provider availability and metadata can change; do not replace reviewed fixture hashes merely to silence a test. Review source rights, radiometry, grids, masks and expected results again. TLS validation is never disabled. Satellite-provider credentials or private accounts are not used.

## Terms and source links

Sentinel data is made available on a free, full and open basis, subject to the provider's legal notice. Modified data must retain attribution; project MIT licensing does **not** relicense the imagery or imply provider endorsement. See the [official Copernicus terms](https://sentiwiki.copernicus.eu/web/terms-and-conditions), [Sentinel-2 mission/data information](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2), and [provider registry/access/citation information](https://registry.opendata.aws/sentinel-2-l2a-cogs/). Exact item URLs and original license links are preserved in the STAC responses.

The seven synthetic cases are original, deterministic arrays by Jason Stys. Their rectangular truth masks are software-test oracles, not satellite ground truth or a model trained on public observations. No personal data, user accounts, private images or real mission telemetry is included.

# FIELDNOTE user guide

Created by Jason Stys. Use this as an offline environmental-imagery review tool, not an automated event verdict.

## First comparison

Launch the complete extracted portable folder, or build/run source as described in the README. Keep its console open. The browser connects to an ephemeral `127.0.0.1` address; Ctrl+C in that console stops only this application. Closing the tab does not stop the server.

1. Start with **Central Valley / Sentinel-2**. It compares April and July 2020 public imagery. Attribution, both dates and the lack of independent ground truth stay visible.
2. Read the verification status and comparable-pixel count. Gray checker pixels are **excluded**, not unchanged land. Pixel accounting must pass before results are displayed.
3. Use **Before / after swipe** and the split slider, or view either date separately. Zoom 1× fits the crop; larger zooms allow scrolling. Both dates use the same fixed display stretch.
4. Select **Candidate overlay**. Blue means index increase; rust means decrease. Gold marks above-threshold cells removed by the minimum-region filter. These are numerical index changes, not land-cover/event labels.
5. Click a pixel, or use the zero-based row/column fields with your keyboard. Inspect exact before/after ratios, comparable delta and projected cell-centre coordinates. A cloud-affected pixel may have a raw ratio but no comparable delta.

## Explore an independently known answer

Choose **Synthetic vegetation loss**. Its 12×16 changed rectangle has 192 pixels, one decrease region and 1.92 nominal hectares at 10 m spacing. At the default settings it has synthetic IoU 1.000. This confirms a software case, not real-image accuracy. **Synthetic water expansion** increases green/NIR NDWI; it should not be interpreted as proving that every real NDWI increase is water.

The **Cloud and shadow trap** puts the apparent change under excluded classes: it should not generate a retained candidate. **Shifted grid / unchanged** exercises coordinate alignment, not array-position comparison. **No comparable pixels** and **Zero denominator** show unavailable rates and scores; no fabricated zero-change rate is shown.

## Understand the controls

- NDVI and green/NIR NDWI answer different spectral questions; neither directly classifies event cause.
- Threshold is absolute index difference, with 0.10/0.20/0.30 choices. Sensitivity shows raw counts before component filtering, not a confidence interval.
- Quality margin excludes a square radius around any incomparable pixel, including outside-crop edges. It is measured in target pixels, not a calibrated cloud uncertainty distance.
- Minimum region size filters four-connected **same-direction** candidates; diagonal/opposite-sign cells do not merge.
- Strict SCL retains classes 4,5,6. Allowing unclassified class 7 is an explicit less-conservative choice, not improved accuracy.
- Remembering controls is opt-in browser storage. Disable the checkbox to remove saved preferences; review notes are never saved there.

## Human review and downloads

Select a region, record a disposition and an optional non-sensitive note, then choose **Record in this tab**. This affects only this page's memory. Changing analysis clears reviews. Download review JSON if you want a local copy; it binds all dispositions to the exact report hash and region IDs. Accepting a candidate means it warrants investigation, not that the application has established an environmental event.

The review menu shows the first 100 regions if a fragmented input has more; the notice makes this explicit. All regions remain in full JSON, CSV and GeoJSON exports. Reports/downloads retain the exclusions and methodological limits. GeoTIFF preserves class/region rasters on the reference grid; GeoJSON footprints use WGS84 longitude/latitude. Do not infer area from degrees or call the nominal UTM area a survey measurement.

## Local inputs, privacy and troubleshooting

Custom supported TIFF pairs are CLI-only; see [API](API.md). Normalize reflectance correctly once, retain attribution, verify complete byte hashes and provide chronological UTC dates. The app is not a malicious-file quarantine system or arbitrary-format converter. Optional SQLite history is explicit, unencrypted and capped at 100 distinct reports. Keep private files/notes outside Git and back them up yourself.

If analysis fails, old evidence disappears. Check the finite selector/input contract, preserve a small synthetic reproduction and retry. Missing assets require `npm ci` then `npm run build` for source launches. A blocked unsigned executable is not a reason to disable OS protection: verify its checksum and use reviewed source if your policy requires it. For an occupied port, omit `--port` instead of stopping unrelated services.

Help: [Jason Stys](https://github.com/JasonStys) · [Project issues](https://github.com/JasonStys/earth-observation-change-studio/issues). Share synthetic reproductions only; no private imagery, account credentials or personal data. Read [MODEL](MODEL.md) before interpreting real observations.

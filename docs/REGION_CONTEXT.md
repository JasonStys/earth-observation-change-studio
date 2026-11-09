# Inspect candidate-region context

Select a candidate region to inspect the unique **four-neighbor fringe pixels** immediately outside its retained footprint: excluded, unchanged, other retained candidates and small filtered candidates. Crop-edge sides are counted separately because outside-crop evidence is unknown. Diagonals do not belong to this defined ring. A pixel touching several cells of one region counts once; rings from different regions can overlap and must not be added as disjoint scene totals.

The context is called complete only when the immediate ring contains no excluded pixels and the region touches no crop edge. This is local availability, not proof of image registration, cloud removal, environmental cause or overall confidence. It flags a useful review question: does unavailable surrounding evidence truncate or obscure the apparent change? The spectral classes, quality masks, thresholds, connectivity and candidate geometry are unchanged.

Region information, full JSON/HTML, geographic GeoJSON properties, tab-local review export and immutable CLI history retain the same report-bound context. The actual GeoTIFF class/region raster remains unchanged. Existing vector/scalar index agreement and pixel-membership/accounting gates remain mandatory. Public Sentinel provenance is retained; no operational surveillance, identity inference or targeting is added.

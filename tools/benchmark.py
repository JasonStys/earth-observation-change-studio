"""Measured numerical contracts and runtime observations by Jason Stys.

Function: main. Variables: fixed defaults, summary tolerances, tracemalloc and descriptive timings.
Index: docs/CODE_INDEX.md. A measured Python peak is not whole-process/GDAL memory or operational accuracy.
"""

import argparse
import json
import math
import statistics
import time
import tracemalloc
from pathlib import Path

from eostudio.engine import build_run, canonical
from eostudio.model import CASES, Settings


def main() -> None:
    """Check reviewed summaries for all eight cases; report repeatable workloads without hard timing gates."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    actual = [{"scenario": name, "summary": build_run(Settings(name))["summary"]} for name in CASES]
    path = Path("docs/reports/benchmark.json")
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            canonical(
                {
                    "schema": 1,
                    "absolute_tolerance": 1e-6,
                    "relative_tolerance": 1e-8,
                    "cases": actual,
                }
            )
        )
    expected = json.loads(path.read_bytes())
    assert expected["schema"] == 1 and len(expected["cases"]) == 8
    assert expected["absolute_tolerance"] == 1e-6 and expected["relative_tolerance"] == 1e-8
    for current, reference in zip(actual, expected["cases"], strict=True):
        assert current["scenario"] == reference["scenario"] and set(current["summary"]) == set(
            reference["summary"]
        )
        for key, value in current["summary"].items():
            target = reference["summary"][key]
            assert (
                value is None
                and target is None
                or value is not None
                and target is not None
                and math.isclose(value, target, rel_tol=1e-8, abs_tol=1e-6)
            ), (key, value, target)
    times = []
    tracemalloc.start()
    for _ in range(5):
        start = time.perf_counter()
        build_run()
        times.append((time.perf_counter() - start) * 1000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(
        f"Eight numerical contracts passed; median {statistics.median(times):.3f} ms; Python traced peak {peak} bytes including scalar/reference/report overhead, not GDAL/native RSS or a real-time guarantee"
    )


if __name__ == "__main__":
    main()

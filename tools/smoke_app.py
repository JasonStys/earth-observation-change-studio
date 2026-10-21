"""Exercise only a newly built or reviewed downloaded app by Jason Stys.

Functions: main, read_output. Variables: owned process, notices, actual exports/SQL and HTTP requests.
Line locations: docs/CODE_INDEX.md. This is not a tool for executing archived Actions evidence.
"""

import json
import queue
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path


def main(executable: Path) -> None:
    """Require real public-source and known-answer results, coordinate export and bundled license data."""
    executable = executable.resolve(strict=True)
    internal = executable.parent / "_internal"
    assert "Vite core license" in (internal / "licenses/vite/LICENSE.md").read_text(
        encoding="utf-8"
    )
    for package in ("rasterio", "numpy"):
        assert list(internal.glob(package + "-*.dist-info/licenses/LICENSE*")), package
    assert (internal / "rasterio/gdal_data/LICENSE.TXT").is_file()
    assert "Frank Warmerdam" in (internal / "licenses/proj/PROJ.txt").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="earth-smoke-") as directory:
        output = Path(directory) / "report.json"
        subprocess.run(
            [
                str(executable),
                "export",
                "--scenario",
                "vegetation-loss",
                "--output",
                str(output),
                "--history",
                str(Path(directory) / "private.sqlite3"),
            ],
            check=True,
            timeout=30,
        )
        run = json.loads(output.read_bytes())
        assert run["summary"]["candidate_pixels"] == 192 and run["truth"]["iou"] == 1
        geo = Path(directory) / "candidates.geojson"
        subprocess.run(
            [
                str(executable),
                "export",
                "--scenario",
                "vegetation-loss",
                "--format",
                "geojson",
                "--output",
                str(geo),
            ],
            check=True,
            timeout=30,
        )
        assert len(json.loads(geo.read_bytes())["features"]) == 1
    process = subprocess.Popen(
        [str(executable), "serve", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines: queue.Queue[str] = queue.Queue()

    def read_output() -> None:
        """Read startup lines off-thread to preserve bounded app-launch timeouts."""
        assert process.stdout is not None
        for line in process.stdout:
            lines.put(line.strip())

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    try:
        url = ""
        for _ in range(8):
            line = lines.get(timeout=15)
            if line.startswith("http://127.0.0.1:"):
                url = line
                break
        assert url
        for route in ("api/health", "", "api/run"):
            with urllib.request.urlopen(url + route, timeout=30) as response:
                data = response.read()
                if route == "":
                    assert b"FIELDNOTE" in data and b"/assets/" in data
                elif route == "api/run":
                    result = json.loads(data)
                    assert result["summary"]["pixels"] == 16384 and result["truth"] is None
                    assert result["method"]["reference_verified"]
                else:
                    assert json.loads(data)["status"] == "ok"
        print(
            "Frozen app passed: actual geospatial runtime/notices, synthetic truth, SQL, WGS84 export, public crop and production HTTP UI"
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        reader.join(timeout=3)
        if process.stdout:
            process.stdout.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]))

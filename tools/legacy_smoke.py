"""Exercise only a newly built or reviewed downloaded app by Jason Stys.

Functions: main, read_output. Variables: owned process, notices, actual exports/SQL and HTTP requests.
Line locations: docs/CODE_INDEX.md. This is not a tool for executing archived Actions evidence.
Preserved domain acceptance; canonical process/version/browser proof is in smoke_app.py."""

import json
import queue
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

if __package__:
    from .release_contract import require
else:
    from release_contract import require


class RefuseRedirects(urllib.request.HTTPRedirectHandler):
    """A local application check never follows an HTTP redirect to another listener or origin."""

    def redirect_request(self, *args, **kwargs):
        """Abort before urllib can issue the redirected request."""
        raise ValueError("Local native acceptance refuses redirects")


OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), RefuseRedirects())


def main(executable: Path) -> None:
    """Require real public-source and known-answer results, coordinate export and bundled license data."""
    executable = executable.resolve(strict=True)
    internal = executable.parent / "_internal"
    require(
        bool(
            "Vite core license"
            in (internal / "licenses/vite/LICENSE.md").read_text(encoding="utf-8")
        ),
        "Preserved native acceptance check failed",
    )
    for package in ("rasterio", "numpy"):
        require(bool(list(internal.glob(package + "-*.dist-info/licenses/LICENSE*"))), package)
    require(
        bool((internal / "rasterio/gdal_data/LICENSE.TXT").is_file()),
        "Preserved native acceptance check failed",
    )
    require(
        bool(
            "Frank Warmerdam" in (internal / "licenses/proj/PROJ.txt").read_text(encoding="utf-8")
        ),
        "Preserved native acceptance check failed",
    )
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
        require(
            bool(run["summary"]["candidate_pixels"] == 192 and run["truth"]["iou"] == 1),
            "Preserved native acceptance check failed",
        )
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
        require(
            bool(len(json.loads(geo.read_bytes())["features"]) == 1),
            "Preserved native acceptance check failed",
        )
    process = subprocess.Popen(
        [str(executable), "serve", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines: queue.Queue[str] = queue.Queue()

    def read_output() -> None:
        """Read startup lines off-thread to preserve bounded app-launch timeouts."""
        require(bool(process.stdout is not None), "Preserved native acceptance check failed")
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
        require(bool(url), "Preserved native acceptance check failed")
        for route in ("api/health", "", "api/run"):
            with OPENER.open(url + route, timeout=30) as response:
                data = response.read()
                if route == "":
                    require(
                        bool(b"FIELDNOTE" in data and b"/assets/" in data),
                        "Preserved native acceptance check failed",
                    )
                elif route == "api/run":
                    result = json.loads(data)
                    require(
                        bool(result["summary"]["pixels"] == 16384 and result["truth"] is None),
                        "Preserved native acceptance check failed",
                    )
                    require(
                        bool(result["method"]["reference_verified"]),
                        "Preserved native acceptance check failed",
                    )
                else:
                    require(
                        bool(json.loads(data)["status"] == "ok"),
                        "Preserved native acceptance check failed",
                    )
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

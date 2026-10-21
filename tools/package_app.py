"""Freeze and smoke-test reviewed offline geospatial bundles by Jason Stys.

Function: main. Variables: fixed resources, runtime notice copies, platform executable and ZIP digest.
Exact lines: docs/CODE_INDEX.md. No installer, elevation, account setup or automatic publication.
"""

import hashlib
import platform
import shutil
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path


def main() -> None:
    """Bundle the locked native geospatial wheels and their notices, test the actual executable, then zip."""
    root = Path(__file__).resolve().parents[1]
    if not (root / "web/dist/index.html").is_file():
        raise SystemExit("Build production web assets first")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--console",
        "--name",
        "EarthObservationStudio",
        "--collect-all",
        "rasterio",
        "--collect-data",
        "numpy",
        "--recursive-copy-metadata",
        "rasterio",
    ]
    for source, destination in (
        ("web/dist", "web/dist"),
        ("eostudio/resources", "eostudio/resources"),
        ("LICENSE", "licenses/project"),
        ("licenses/PYTHON.txt", "licenses/python"),
        ("docs/THIRD_PARTY.md", "docs"),
        ("docs/DATA.md", "docs"),
        ("node_modules/vite/LICENSE.md", "licenses/vite"),
    ):
        command.extend(["--add-data", source + ":" + destination])
    pyinstaller = distribution("pyinstaller")
    notices = [
        pyinstaller.locate_file(path)
        for path in pyinstaller.files or []
        if str(path).endswith("licenses/COPYING.txt")
    ]
    if len(notices) != 1:
        raise SystemExit("Expected the locked PyInstaller notice")
    command.extend(["--add-data", str(notices[0]) + ":licenses/pyinstaller"])
    # These actual runtime notices accompany collected GCC libraries on the Ubuntu/Debian runner.
    if sys.platform == "linux":
        for notice in (
            "/usr/share/doc/libstdc++6/copyright",
            "/usr/share/doc/libgcc-s1/copyright",
            "/usr/share/common-licenses/GPL-3",
        ):
            source = Path(notice)
            if not source.is_file():
                raise SystemExit("Expected GCC runtime distribution notices")
            command.extend(
                ["--add-data", str(source) + ":licenses/compiler-runtime/" + source.parent.name]
            )
    command.append("launcher.py")
    subprocess.run(command, cwd=root, check=True, timeout=600)
    executable = (
        root
        / "dist/EarthObservationStudio"
        / ("EarthObservationStudio.exe" if sys.platform == "win32" else "EarthObservationStudio")
    )
    subprocess.run(
        [sys.executable, "tools/smoke_app.py", str(executable)], cwd=root, check=True, timeout=120
    )
    slug = (
        f"earth-observation-change-studio-{platform.system().lower()}-{platform.machine().lower()}"
    )
    archive = Path(
        shutil.make_archive(
            str(root / "dist" / slug), "zip", root / "dist", "EarthObservationStudio"
        )
    )
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    (root / "dist" / (slug + ".sha256")).write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Verified portable bundle: {archive.name} SHA-256 {digest}")


if __name__ == "__main__":
    main()

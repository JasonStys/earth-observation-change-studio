"""Fail-closed draft release preparation by Jason Stys.

Function: main. Variables: version, sha, repository, workflow runs. Index: docs/CODE_INDEX.md.
Only the exact current commit's successful Validation and CodeQL runs authorize packaging.
"""

import json
import os
import re
import subprocess


def main() -> None:
    """Validate version, require successful exact-commit workflows, create a new draft only."""
    version = os.environ["VERSION"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise SystemExit("Expected digits.digits.digits")
    sha, repository = os.environ["GITHUB_SHA"], os.environ["GITHUB_REPOSITORY"]
    for workflow in ("validate.yml", "codeql.yml"):
        result = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repository}/actions/workflows/{workflow}/runs?head_sha={sha}&per_page=20",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        runs = json.loads(result.stdout)["workflow_runs"]
        if not runs or runs[0]["conclusion"] != "success":
            raise SystemExit(f"{workflow} has not passed at {sha}")
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            f"v{version}",
            "--repo",
            repository,
            "--target",
            sha,
            "--draft",
            "--title",
            f"Earth Observation Change Studio v{version}",
            "--notes",
            "Unsigned offline environmental imagery review by Jason Stys. Extract the entire ZIP and verify SHA-256. Spectral candidates require human context; not confirmed events or operational surveillance. Contains modified Copernicus Sentinel data (2020). Do not bypass OS warnings; see source and model limits.",
        ],
        check=True,
        timeout=30,
    )


if __name__ == "__main__":
    main()

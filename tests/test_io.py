"""Real loopback, CLI and immutable SQL history acceptance by Jason Stys.

Functions cover finite routes, same-origin checks, filesystem confinement, failures and persistence.
Variables/line inventory: docs/CODE_INDEX.md. All writes are task-owned temporary synthetic evidence.
"""

import http.client as client
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import pytest

from eostudio import __main__ as cli
from eostudio import server as http
from eostudio.engine import canonical, run_id
from eostudio.model import RESOURCES
from eostudio.reports import save_history


@pytest.fixture
def service(tmp_path):
    """Start and reliably stop only this test's ephemeral-port loopback service and synthetic assets."""
    assets = tmp_path / "assets-root"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html><title>Test asset only</title>")
    (assets / "assets").mkdir()
    (assets / "assets" / "valid.js").write_text("// inert synthetic route fixture")
    instance = http.make_server(assets)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        yield instance
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=3)


def request(service, path, method="GET", headers=None):
    """Use a real socket with a deadline and exact Host to exercise HTTP parsing and response bytes."""
    connection = client.HTTPConnection("127.0.0.1", service.server_port, timeout=15)
    try:
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/index.html",
        "/assets/valid.js",
        "/api/health",
        "/api/catalog",
        "/api/run?scenario=no-change",
        "/api/report?scenario=vegetation-loss&format=tif",
        "/api/report?scenario=water-gain&metric=ndwi&format=geojson",
    ],
)
def test_valid_routes_and_headers(service, path):
    """Actual successful routes return restrictive security headers, including binary-specific MIME."""
    status, headers, body = request(service, path)
    assert status == 200 and body
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Cache-Control"] == "no-store"
    assert "Access-Control-Allow-Origin" not in headers
    if "format=tif" in path:
        assert headers["Content-Type"] == "image/tiff"
        assert body[:2] in (b"II", b"MM")
    if "/api/report" in path:
        assert headers["Content-Disposition"].startswith("attachment;")


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "evil.invalid"},
        {"Origin": "https://evil.invalid"},
        {"Sec-Fetch-Site": "cross-site"},
    ],
)
def test_host_and_origin(service, headers):
    """DNS-rebinding/cross-origin browser requests are rejected without reflecting attacker text."""
    status, _, body = request(service, "/api/run", headers=headers)
    assert status == 403 and b"evil" not in body


@pytest.mark.parametrize(
    "path,status",
    [
        ("/api/run?scenario=unknown", 400),
        ("/api/run?threshold=True", 400),
        ("/api/run?margin=8", 400),
        ("/api/run?format=json", 400),
        ("/api/report?format=bad", 400),
        ("/api/run?scenario=no-change&scenario=all-masked", 400),
        ("/api/run?extra=1", 400),
        ("/api/run?" + "&".join("x=1" for _ in range(9)), 400),
        ("/api/health?x=1", 404),
        ("/.env", 404),
        ("/../LICENSE", 404),
        ("/assets/%2e%2e/license.js", 404),
        ("/assets/../../outside.js", 404),
        ("/assets\\outside.js", 404),
        ("/assets/nope.js", 404),
        ("/assets/file.exe", 404),
        ("/" + "x" * 1025, 414),
    ],
)
def test_request_boundaries(service, path, status):
    """Queries, formats, traversal, secret/source paths and request-size envelopes fail closed."""
    assert request(service, path)[0] == status


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
def test_no_http_mutations(service, method):
    """Every state-changing route is absent; browser review never writes a server database."""
    assert request(service, "/api/run", method=method)[0] == 405


def test_service_failure_and_same_origin(service, monkeypatch):
    """Local numerical/resource failures return controlled responses; exact same origin is allowed."""
    origin = f"http://127.0.0.1:{service.server_port}"
    assert request(service, "/api/health", headers={"Origin": origin})[0] == 200

    def unavailable(*args):
        """Simulate an unavailable numerical resource without leaking local filesystem information."""
        raise RuntimeError("private-local-path")

    monkeypatch.setattr(http, "build_run", unavailable)
    status, _, body = request(service, "/api/run")
    assert status == 500 and b"private" not in body


def evidence(number):
    """Create small hash-valid synthetic history entries to test SQL policy without huge rasters."""
    result = {"name": "synthetic", "iteration": number}
    result["id"] = run_id(result)
    return result


def test_history_identity_immutability_and_capacity(tmp_path):
    """Hash mismatch, edits and a 101st distinct insertion fail; duplicates are idempotent."""
    path = tmp_path / "private.sqlite3"
    for index in range(100):
        save_history(path, evidence(index))
    save_history(path, evidence(0))
    with pytest.raises(ValueError, match="full"):
        save_history(path, evidence(100))
    with pytest.raises(ValueError, match="hash"):
        save_history(path, {"name": "forged", "id": "x"})
    with closing(sqlite3.connect(path)) as db:
        assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 100
        for query in ("UPDATE runs SET scenario='x'", "DELETE FROM runs"):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(query)


def test_history_concurrency(tmp_path):
    """Concurrent duplicate insertion has one immutable stored identity, not lost/duplicated rows."""
    path = tmp_path / "private.sqlite3"
    save_history(path, evidence(1))
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: save_history(path, evidence(1)), range(8)))
    with closing(sqlite3.connect(path)) as db:
        assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 1


def test_cli_exports_create_only_and_controlled_failures(tmp_path, capsys):
    """Real CLI export/history works; duplicate files and invalid local data do not overwrite evidence."""
    path = tmp_path / "report.json"
    args = [
        "export",
        "--scenario",
        "vegetation-loss",
        "--output",
        str(path),
        "--history",
        str(tmp_path / "history.sqlite3"),
    ]
    assert cli.main(args) == 0
    original = path.read_bytes()
    assert json.loads(original)["summary"]["candidate_pixels"] == 192
    assert cli.main(args) == 1 and path.read_bytes() == original
    invalid = tmp_path / "bad.json"
    invalid.write_text("{}")
    assert (
        cli.main(["export", "--input", str(invalid), "--output", str(tmp_path / "other.json")]) == 1
    )
    assert not (tmp_path / "other.json").exists()
    assert "Cannot complete" in capsys.readouterr().err


def test_cli_server_stop_and_missing_assets(tmp_path, monkeypatch):
    """Launcher teardown handles keyboard interruption; missing packaged assets are a real error."""
    assets = tmp_path / "web/dist"
    assets.mkdir(parents=True)
    (assets / "index.html").write_text("<!doctype html><title>fixture</title>")
    monkeypatch.setattr(cli.sys, "_MEIPASS", str(tmp_path), raising=False)
    called = []
    monkeypatch.setattr(cli.webbrowser, "open", called.append)

    def interrupted(self, **kwargs):
        """Stop only the test's owned server instead of blocking the suite."""
        raise KeyboardInterrupt

    monkeypatch.setattr(http.WorkbenchServer, "serve_forever", interrupted)
    assert cli.main(["serve"]) == 0 and len(called) == 1
    assert cli.main(["serve", "--no-browser"]) == 0 and len(called) == 1
    monkeypatch.setattr(cli.sys, "_MEIPASS", str(tmp_path / "missing"))
    assert cli.main(["serve", "--no-browser"]) == 1


def test_disconnect_does_not_try_second_reply(monkeypatch):
    """An aborted browser socket is caught once, with no cascading response/write attempt."""
    handler = object.__new__(http.Handler)
    handler.command = "GET"
    monkeypatch.setattr(handler, "send_response", lambda *args: None)
    monkeypatch.setattr(handler, "send_header", lambda *args: None)

    def disconnected():
        """Simulate header flushing after the client has disconnected."""
        raise ConnectionResetError

    monkeypatch.setattr(handler, "end_headers", disconnected)
    handler.reply(200, b"x", "text/plain")
    assert canonical(evidence(0))


def test_cli_valid_public_manifest(tmp_path):
    """A real bounded custom-file pair runs through the CLI, not just direct loader tests."""
    output = tmp_path / "imported.json"
    assert (
        cli.main(
            [
                "export",
                "--input",
                str(RESOURCES / "sentinel/central-valley.json"),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    run = json.loads(output.read_bytes())
    assert run["name"] == "central-valley" and run["truth"] is None
    assert run["summary"]["pixels"] == 16384

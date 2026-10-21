"""Local application launcher and explicit evidence exports by Jason Stys.

Function: main. Variables: finite controls, explicit local input/output/history and loopback service.
Exact line inventory: docs/CODE_INDEX.md. No account, public bind, shell or live device connection.
"""

import argparse
import sqlite3
import sys
import webbrowser
from pathlib import Path

from eostudio.engine import analyze, build_run
from eostudio.model import CASES, CHOICES, Settings, load_pair
from eostudio.reports import export_report, save_history
from eostudio.server import make_server


def main(argv: list[str] | None = None) -> int:
    """Run the local UI or export one verified finite case; never overwrite an existing destination."""
    parser = argparse.ArgumentParser(description="Earth Observation Change Studio by Jason Stys")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Start the read-only local browser application")
    serve.add_argument("--port", type=int, default=0)
    serve.add_argument("--no-browser", action="store_true")
    export = commands.add_parser("export", help="Save verified synthetic evidence")
    export.add_argument("--scenario", choices=CASES, default=Settings().scenario)
    for key, choices in CHOICES.items():
        export.add_argument(
            "--" + key, type=type(choices[0]), choices=choices, default=getattr(Settings(), key)
        )
    export.add_argument("--input", type=Path)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--history", type=Path)
    export.add_argument(
        "--format", choices=("json", "csv", "html", "geojson", "tif"), default="json"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "export":
            if args.output.exists():
                raise FileExistsError("Export destination already exists")
            settings = Settings(**{key: getattr(args, key) for key in ("scenario", *CHOICES)})
            run = analyze(load_pair(args.input), settings) if args.input else build_run(settings)
            body, _ = export_report(run, args.format)
            if args.history:
                save_history(args.history, run)
            with args.output.open("xb") as destination:
                destination.write(body)
            print(f"Saved {run['id']}")
            return 0
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        assets = root / "web/dist"
        if not (assets / "index.html").is_file():
            raise OSError("Build website assets first: npm ci and npm run build")
        with make_server(assets, args.port) as server:
            url = f"http://127.0.0.1:{server.server_port}/"
            print(f"Earth Observation Change Studio by Jason Stys\n{url}", flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            try:
                server.serve_forever(poll_interval=0.25)
            except KeyboardInterrupt:
                print("Earth observation studio stopped.", flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        print(f"Cannot complete operation: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

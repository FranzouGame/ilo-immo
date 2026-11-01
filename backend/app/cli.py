"""CLI : python -m app.cli ingest [source] | recompute | seed-demo | export-static OUT.json [PREVIOUS.json]"""
import json
import logging
import sys
from pathlib import Path

from app.compute import recompute_all
from app.connectors.base import ListingConnector
from app.connectors.registry import build, is_enabled, load_all
from app.db import SessionLocal


def ordered(names: list[str]) -> list[str]:
    """Annonces d'abord, puis enrichissements (BAN, DPE, risques), puis données de référence (DVF, OSM…)."""
    reg = load_all()
    rank = lambda n: 0 if issubclass(reg[n], ListingConnector) else (1 if n in ("ban", "dpe", "georisques") else 2)  # noqa: E731
    return sorted(names, key=rank)


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cmd = argv[0] if argv else "help"
    with SessionLocal() as s:
        if cmd == "ingest":
            names = [argv[1]] if len(argv) > 1 else ordered([n for n in load_all() if is_enabled(n)])
            for n in names:  # une source nommée explicitement est lancée même si désactivée
                run = build(n, s).run()
                print(f"{n}: {run.status} ({run.n_records}) {run.message}")
            print(f"{recompute_all(s)} biens recalculés")
        elif cmd == "recompute":
            print(f"{recompute_all(s)} biens recalculés")
        elif cmd == "export-static" and len(argv) > 1:
            from app.config import app_config
            from app.export_static import export
            prev = json.loads(Path(argv[2]).read_text("utf-8")) if len(argv) > 2 and Path(argv[2]).exists() else None
            data = export(s, prev, include_photos=bool(app_config().get("static_export", {}).get("include_photos")))
            Path(argv[1]).write_text(json.dumps(data, ensure_ascii=False), "utf-8")
            print(f"{len(data['items'])} annonces exportées")
        elif cmd == "seed-demo":
            from app.demo import seed
            print(f"{seed(s)} biens de démonstration")
        else:
            print(__doc__)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

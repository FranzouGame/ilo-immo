"""CLI : python -m app.cli ingest [source] | recompute | seed-demo"""
import logging
import sys

from app.compute import recompute_all
from app.connectors.registry import build, is_enabled, load_all
from app.db import SessionLocal


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cmd = argv[0] if argv else "help"
    with SessionLocal() as s:
        if cmd == "ingest":
            names = [argv[1]] if len(argv) > 1 else [n for n in load_all() if is_enabled(n)]
            for n in names:  # une source nommée explicitement est lancée même si désactivée
                run = build(n, s).run()
                print(f"{n}: {run.status} ({run.n_records}) {run.message}")
            print(f"{recompute_all(s)} biens recalculés")
        elif cmd == "recompute":
            print(f"{recompute_all(s)} biens recalculés")
        elif cmd == "seed-demo":
            from app.demo import seed
            print(f"{seed(s)} biens de démonstration")
        else:
            print(__doc__)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

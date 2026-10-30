import importlib
import pkgutil

from sqlalchemy.orm import Session

import app.connectors as pkg
import app.connectors.listings as listings_pkg
from app.config import app_config
from app.connectors.base import REGISTRY, Connector


def load_all() -> dict[str, type[Connector]]:
    for p in (pkg, listings_pkg):
        for m in pkgutil.iter_modules(p.__path__):
            importlib.import_module(f"{p.__name__}.{m.name}")
    return REGISTRY


def build(name: str, session: Session) -> Connector:
    cfg = app_config()
    return load_all()[name](cfg["connectors"].get(name, {}), cfg, session)


def is_enabled(name: str) -> bool:
    return bool(app_config()["connectors"].get(name, {}).get("enabled"))

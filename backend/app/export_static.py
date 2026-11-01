"""Export statique (GitHub Pages) : un JSON public avec les annonces collectées, sans rien de personnel.

Exclus volontairement : annonces saisies à la main/démo, statuts et notes, âge/sexe des vendeurs de viager, et (par défaut) les photos."""
from datetime import UTC, datetime
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import app_config
from app.connectors.base import ListingConnector
from app.connectors.registry import load_all
from app.models import Property
from app.search import prop_dict

PRIVATE_KEYS = ("notes", "status", "breakdown", "score", "source_url")


def export(session: Session, previous: dict[str, Any] | None = None, include_photos: bool = False) -> dict[str, Any]:
    cfg = app_config()
    sources = [n for n, c in load_all().items() if issubclass(c, ListingConnector) and n != "notaires"]
    first_seen = {i["url"]: i["created_at"] for i in (previous or {}).get("items", []) if i.get("url")}
    items = []
    for p in session.scalars(select(Property).where(Property.source.in_(sources), Property.gone.is_(False)).order_by(Property.id)):
        d = prop_dict(p)
        for k in PRIVATE_KEYS:
            d.pop(k, None)
        d["status"], d["notes"] = "a_voir", ""
        if not include_photos:
            d["photos"] = []
        viager = d["custom"].get("viager")
        if isinstance(viager, dict):
            viager.pop("ages", None)  # âge et sexe des vendeurs : pas de republication
        d["created_at"] = first_seen.get(d["url"]) or d["created_at"]
        items.append(jsonable_encoder(d))
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "config": {"departments": [{"code": x["code"], "name": x["name"]} for x in cfg["departments"]],
                   "department_name": " · ".join(x["name"] for x in cfg["departments"]), "map": cfg["map"],
                   "criteria": cfg["scoring"]["criteria"]},
        "defaults": cfg["scoring"]["simple"], "items": items,
    }

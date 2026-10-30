from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import app_config
from app.connectors.common import lonlat
from app.models import Property
from app.scoring import Spec, evaluate, matches_basic

COLUMNS = ["id", "source", "url", "title", "type", "price", "surface", "land_surface", "rooms", "floor", "floors_total",
           "balcony", "elevator", "orientation", "year_built", "address", "commune", "postcode", "insee", "dpe", "ges",
           "condition", "status", "notes", "tags", "custom", "manual_view", "manual_light", "manual_vis_a_vis", "photos"]


def kind_of(p: Property) -> str:
    tags = p.tags or []
    if "enchère" in tags:
        return "enchere"
    if "viager" in tags:
        return "viager"
    if "vente interactive" in tags:
        return "interactive"
    if p.source in ("programmes",):
        return "aide"
    return "autre"


def prop_dict(p: Property) -> dict[str, Any]:
    d: dict[str, Any] = {c: getattr(p, c) for c in COLUMNS}
    d["computed"] = p.computed or {}
    ll = lonlat(p)
    d["lon"], d["lat"] = ll if ll else (None, None)
    d["kind"] = kind_of(p)
    d["price_m2"] = round(p.price / p.surface) if p.price and p.surface else None
    d["created_at"], d["updated_at"] = p.created_at, p.updated_at
    return d


def search(session: Session, spec: Spec) -> list[dict[str, Any]]:
    cfg = app_config()
    out = []
    for p in session.scalars(select(Property)):
        d = prop_dict(p)
        if not matches_basic(d, spec):
            continue
        ev = evaluate(d, spec, cfg)
        if ev["passes"]:
            out.append({**d, "score": ev["score"], "near": ev["near"], "breakdown": ev["breakdown"]})
    key = spec.get("sort", "score")
    reverse = spec.get("order", "desc") == "desc"
    out.sort(key=lambda r: (r.get(key) is None, r.get(key) or 0), reverse=reverse)
    # les valeurs absentes restent en fin de liste quel que soit l'ordre
    out.sort(key=lambda r: r.get(key) is None)
    return out

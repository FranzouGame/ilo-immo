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
FEED_DAYS = 14


def merge_history(prev: dict[str, Any] | None, price: float | None, today: str) -> list[dict[str, Any]]:
    """Historique des anciens prix : celui de la version précédente du site + l'ancien prix si le prix a changé."""
    hist = list((prev or {}).get("price_history") or [])
    old = (prev or {}).get("price")
    if old and price and abs(old - price) > 0.5:
        hist.append({"date": today, "price": old})
    return hist


def feed_xml(items: list[dict[str, Any]], site_url: str, now: datetime) -> str:
    """Flux Atom : nouvelles annonces et baisses de prix des 14 derniers jours (lisible par n'importe quel lecteur RSS)."""
    from xml.sax.saxutils import escape
    cutoff = (now.date().toordinal() - FEED_DAYS)
    entries = []
    for i in items:
        first = datetime.fromisoformat(i["created_at"]).date()
        hist = i.get("price_history") or []
        last = hist[-1] if hist else None
        event = None
        if first.toordinal() >= cutoff:
            event = ("Nouveau", first.isoformat())
        elif last and datetime.fromisoformat(last["date"]).date().toordinal() >= cutoff and i["price"]:
            pct = round(100 * (i["price"] - last["price"]) / last["price"])
            event = (f"Prix {'↓' if pct < 0 else '↑'} {abs(pct)} %", last["date"])
        if event:
            entries.append((event[1], f"{event[0]} : {i['title']} - {i['commune']} - {round(i['price'] or 0):,} €".replace(",", " "), i["url"] or site_url))
    body = "".join(f"<entry><title>{escape(t)}</title><link href=\"{escape(u)}\"/><id>{escape(u)}#{d}</id><updated>{d}T00:00:00Z</updated></entry>"
                   for d, t, u in sorted(entries, reverse=True))
    return (f'<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Ilo - nouveautés</title>'
            f'<link href="{escape(site_url)}"/><id>{escape(site_url)}</id><updated>{now.isoformat(timespec="seconds")}</updated>{body}</feed>')


def export(session: Session, previous: dict[str, Any] | None = None, include_photos: bool = False) -> dict[str, Any]:
    cfg = app_config()
    sources = [n for n, c in load_all().items() if issubclass(c, ListingConnector) and n != "notaires"]
    prev_items = {i["url"]: i for i in (previous or {}).get("items", []) if i.get("url")}
    today = datetime.now(UTC).date().isoformat()
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
        prev = prev_items.get(d["url"])
        d["created_at"] = prev["created_at"] if prev else d["created_at"]
        if prev:
            d["price_history"] = merge_history(prev, d["price"], today)
        items.append(jsonable_encoder(d))
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "config": {"departments": [{"code": x["code"], "name": x["name"]} for x in cfg["departments"]],
                   "department_name": " · ".join(x["name"] for x in cfg["departments"]), "map": cfg["map"],
                   "criteria": cfg["scoring"]["criteria"], "finance": cfg["finance"], "fees_pct": cfg["knowledge"]["fees_pct"]},
        "defaults": cfg["scoring"]["simple"], "items": items,
    }

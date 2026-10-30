from typing import Any

from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Property, SourceRecord


def point_sql(lon: float, lat: float) -> Any:
    return func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)


def lonlat(prop: Property) -> tuple[float, float] | None:
    if prop.geom is None:
        return None
    p = to_shape(prop.geom)
    return (p.x, p.y) if isinstance(p, Point) else None


USER_OWNED = {"tags", "notes", "custom", "photos", "status"}


def upsert_properties(session: Session, source: str, records: list[dict[str, Any]]) -> int:
    """Insère/met à jour des biens issus d'un connecteur d'annonces (clé : source + url)."""
    n = 0
    for rec in records:
        raw = rec.pop("raw", {})
        lon, lat = rec.pop("lon", None), rec.pop("lat", None)
        prop = session.scalar(select(Property).where(Property.source == source, Property.url == rec.get("url")))
        if prop is None:
            prop = Property(source=source, computed={}, **{**{'tags': [], 'custom': {}, 'photos': []}, **rec})
            session.add(prop)
            session.flush()
        else:
            for k, v in rec.items():
                if k not in USER_OWNED:  # ne jamais écraser ce que l'utilisateur a saisi
                    setattr(prop, k, v)
        if lon is not None and lat is not None:
            prop.geom = point_sql(lon, lat)
        session.add(SourceRecord(source=source, external_id=rec.get("url") or str(prop.id), property_id=prop.id, payload=raw))
        n += 1
    return n



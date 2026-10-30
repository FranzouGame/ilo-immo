from collections.abc import Iterable, Iterator
from typing import Any

from sqlalchemy import select

from app.connectors.base import Connector
from app.connectors.common import point_sql
from app.http import PoliteClient
from app.models import Property

_http: PoliteClient | None = None


def geocode(url: str, query: str, postcode: str | None = None) -> dict[str, Any] | None:
    """Géocode une adresse via la BAN. -> {lon, lat, label, postcode, insee, city, score} ou None."""
    global _http
    _http = _http or PoliteClient(rate_per_s=10, timeout=20)
    params: dict[str, Any] = {"q": query, "limit": 1}
    if postcode:
        params["postcode"] = postcode
    feats = _http.get_json(url, params=params).get("features", [])
    if not feats:
        return None
    f = feats[0]
    p = f["properties"]
    return {"lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1], "label": p["label"],
            "postcode": p.get("postcode"), "insee": p.get("citycode"), "city": p.get("city"), "score": p.get("score")}


class BanConnector(Connector):
    name = "ban"
    label = "BAN - Base Adresse Nationale (géocodage)"
    license = "Licence Ouverte 2.0 (Etalab)"
    terms_url = "https://adresse.data.gouv.fr/api-doc/adresse"
    update_frequency = "à la demande (biens sans coordonnées)"

    def fetch(self) -> Iterator[list[tuple[int, str, str | None]]]:
        rows = self.session.execute(select(Property.id, Property.address, Property.postcode)
                                    .where(Property.geom.is_(None), Property.address.is_not(None))).all()
        if rows:
            yield [(r[0], str(r[1]), r[2]) for r in rows]

    def normalize(self, raw: list[tuple[int, str, str | None]]) -> Iterable[dict[str, Any]]:
        for pid, addr, cp in raw:
            if g := geocode(self.cfg["url"], addr, cp):
                yield {"id": pid, **g}

    def upsert(self, records: list[dict[str, Any]]) -> int:
        for r in records:
            p = self.session.get(Property, r["id"])
            if p:
                p.geom, p.postcode, p.insee, p.commune = point_sql(r["lon"], r["lat"]), r["postcode"], r["insee"], r["city"]
        return len(records)

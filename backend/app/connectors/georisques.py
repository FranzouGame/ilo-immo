from collections.abc import Iterable, Iterator
from typing import Any

from sqlalchemy import select

from app.connectors.base import Connector
from app.connectors.common import lonlat
from app.http import PoliteClient
from app.models import Property

_http: PoliteClient | None = None


def lookup_risks(url: str, lon: float, lat: float, radius_m: int) -> dict[str, Any]:
    """Risques recensés (GASPAR) autour du point. -> {count, items}"""
    global _http
    _http = _http or PoliteClient(rate_per_s=4, timeout=30)
    data = _http.get_json(url, params={"latlon": f"{lon},{lat}", "rayon": radius_m})
    labels = sorted({d["libelle_risque_long"] for c in data.get("data", []) for d in c.get("risques_detail", [])})
    return {"count": len(labels), "items": labels}


class GeorisquesConnector(Connector):
    name = "georisques"
    label = "Géorisques (inondation, mouvements de terrain, radon…)"
    license = "Licence Ouverte 2.0 (Etalab)"
    terms_url = "https://www.georisques.gouv.fr/doc-api"
    update_frequency = "à la demande (biens sans risques calculés)"

    def fetch(self) -> Iterator[list[tuple[int, float, float]]]:
        out = []
        for p in self.session.scalars(select(Property).where(Property.geom.is_not(None))):
            if "georisks" not in (p.computed or {}) and (ll := lonlat(p)):
                out.append((p.id, *ll))
        if out:
            yield out

    def normalize(self, raw: list[tuple[int, float, float]]) -> Iterable[dict[str, Any]]:
        for pid, lon, lat in raw:
            yield {"id": pid, "georisks": lookup_risks(self.cfg["url"], lon, lat, self.cfg["radius_m"])}

    def upsert(self, records: list[dict[str, Any]]) -> int:
        for r in records:
            p = self.session.get(Property, r["id"])
            if p:
                p.computed = {**(p.computed or {}), "georisks": r["georisks"]}
        return len(records)

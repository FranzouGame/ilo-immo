from collections.abc import Iterable, Iterator
from typing import Any

from sqlalchemy import select

from app.connectors.base import Connector
from app.http import PoliteClient
from app.models import Property

_http: PoliteClient | None = None
FIELDS = "etiquette_dpe,etiquette_ges,adresse_ban,annee_construction,surface_habitable_logement,date_etablissement_dpe"


def lookup_dpe(url: str, address: str, surface: float | None = None) -> dict[str, Any] | None:
    """Cherche un DPE par adresse (ADEME). Retient le DPE à la surface la plus proche, sinon le plus récent."""
    global _http
    _http = _http or PoliteClient(rate_per_s=4, timeout=30)
    data = _http.get_json(url, params={"q": address, "q_fields": "adresse_ban", "size": 20, "select": FIELDS,
                                       "sort": "-date_etablissement_dpe"})
    rows = [r for r in data.get("results", []) if r.get("etiquette_dpe")]
    if not rows:
        return None
    best = min(rows, key=lambda r: abs((r.get("surface_habitable_logement") or 0) - surface)) if surface else rows[0]
    return {"dpe": best["etiquette_dpe"], "ges": best.get("etiquette_ges"),
            "year_built": int(best["annee_construction"]) if best.get("annee_construction") else None,
            "adresse_dpe": best.get("adresse_ban")}


class DpeConnector(Connector):
    name = "dpe"
    label = "DPE - ADEME"
    license = "Licence Ouverte 2.0 (Etalab)"
    terms_url = "https://data.ademe.fr/datasets/dpe03existant"
    update_frequency = "continue (enrichit les biens sans DPE)"

    def fetch(self) -> Iterator[list[tuple[int, str, float | None]]]:
        rows = self.session.execute(select(Property.id, Property.address, Property.surface)
                                    .where(Property.dpe.is_(None), Property.address.is_not(None))).all()
        if rows:
            yield [(r[0], str(r[1]), r[2]) for r in rows]

    def normalize(self, raw: list[tuple[int, str, float | None]]) -> Iterable[dict[str, Any]]:
        for pid, addr, surface in raw:
            if d := lookup_dpe(self.cfg["url"], addr, surface):
                yield {"id": pid, **d}

    def upsert(self, records: list[dict[str, Any]]) -> int:
        for r in records:
            p = self.session.get(Property, r["id"])
            if p:
                p.dpe, p.ges = r["dpe"], r["ges"]
                p.year_built = p.year_built or r["year_built"]
        return len(records)

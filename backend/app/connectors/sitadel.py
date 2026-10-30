import csv
import io
from collections.abc import Iterable, Iterator
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from app.connectors.ban import geocode
from app.connectors.base import Connector
from app.http import PoliteClient
from app.models import ConstructionProject

MIN_DWELLINGS = 10  # on ne géocode que les projets susceptibles de créer un vis-à-vis


class SitadelConnector(Connector):
    name = "sitadel"
    label = "Sitadel - permis de construire"
    license = "Licence Ouverte 2.0 (SDES)"
    terms_url = "https://www.statistiques.developpement-durable.gouv.fr/base-de-donnees-sitadel"
    update_frequency = "mensuelle"
    warning = "L'URL du fichier change à chaque millésime : renseigner connectors.sitadel.url."

    def fetch(self) -> Iterator[list[dict[str, str]]]:
        if not self.cfg.get("url"):
            raise RuntimeError("connectors.sitadel.url vide : renseigner l'URL du CSV Sitadel (logements autorisés)")
        text = PoliteClient(rate_per_s=1, timeout=600).request("GET", self.cfg["url"]).content.decode("utf-8-sig")
        rows = [r for r in csv.DictReader(io.StringIO(text), delimiter=";") if r.get("DEP") in {d["code"] for d in self.app_cfg["departments"]}]
        for i in range(0, len(rows), 200):
            yield rows[i:i + 200]

    def normalize(self, raw: list[dict[str, str]]) -> Iterable[dict[str, Any]]:
        ban = self.app_cfg["connectors"]["ban"]["url"]
        for r in raw:
            n = int(r.get("NB_LGT_TOT_CREES") or 0)
            geom = None
            if n >= MIN_DWELLINGS and r.get("ADR_LIBVOIE_TER"):
                q = " ".join(filter(None, [r.get("ADR_NUM_TER"), r["ADR_LIBVOIE_TER"], r.get("ADR_LOCALITE_TER")]))
                if g := geocode(ban, q, r.get("ADR_CODPOST_TER")):
                    geom = func.ST_SetSRID(func.ST_MakePoint(g["lon"], g["lat"]), 4326)
            d = r.get("DATE_REELLE_AUTORISATION")
            yield {"ext_id": r["Num_DAU"], "insee": r["COMM"][:5], "kind": r.get("TYPE_DAU"), "dwellings": n,
                   "authorized_on": date.fromisoformat(d[:10]) if d else None, "geom": geom}

    def upsert(self, records: list[dict[str, Any]]) -> int:
        if records:
            stmt = insert(ConstructionProject).values(records)
            self.session.execute(stmt.on_conflict_do_nothing(index_elements=["ext_id"]))
        return len(records)

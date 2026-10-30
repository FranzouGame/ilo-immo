import csv
import gzip
import io
from collections import defaultdict
from collections.abc import Iterable, Iterator
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from app.connectors.base import Connector
from app.http import PoliteClient
from app.market import refresh_market_stats
from app.models import Sale

TYPES = {"Appartement": "appartement", "Maison": "maison"}
# Bornes de cohérence pour écarter les valeurs aberrantes (ventes symboliques, erreurs de saisie).
MIN_PRICE, MIN_SURFACE, PPM2_RANGE = 10_000, 9, (500, 30_000)


class DvfConnector(Connector):
    name = "dvf"
    label = "DVF - Demandes de valeurs foncières"
    license = "Licence Ouverte 2.0 (Etalab)"
    terms_url = "https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/"
    update_frequency = "semestrielle"

    def fetch(self) -> Iterator[list[dict[str, str]]]:
        http = PoliteClient(rate_per_s=1, timeout=300)
        for year in self.cfg["years"]:
            url = self.cfg["url_template"].format(year=year, dept=self.app_cfg["department"])
            data = gzip.decompress(http.request("GET", url).content).decode("utf-8")
            by_mutation: dict[str, list[dict[str, str]]] = defaultdict(list)
            for row in csv.DictReader(io.StringIO(data)):
                if row["nature_mutation"] == "Vente" and row["type_local"] in TYPES:
                    by_mutation[row["id_mutation"]].append(row)
            items = [rows for rows in by_mutation.values() if len(rows) == 1]  # mutations à un seul local : sans ambiguïté
            for i in range(0, len(items), self.batch_size):
                yield [r[0] for r in items[i:i + self.batch_size]]

    def normalize(self, raw: list[dict[str, str]]) -> Iterable[dict[str, Any]]:
        for r in raw:
            try:
                price, surface = float(r["valeur_fonciere"]), float(r["surface_reelle_bati"])
            except ValueError:
                continue
            if price < MIN_PRICE or surface < MIN_SURFACE or not PPM2_RANGE[0] <= price / surface <= PPM2_RANGE[1]:
                continue
            lon, lat = r.get("longitude"), r.get("latitude")
            yield {
                "mutation_id": r["id_mutation"], "sold_on": date.fromisoformat(r["date_mutation"]),
                "price": price, "type": TYPES[r["type_local"]], "surface": surface,
                "rooms": int(r["nombre_pieces_principales"] or 0) or None,
                "land_surface": float(r["surface_terrain"]) if r.get("surface_terrain") else None,
                "price_m2": round(price / surface, 1), "insee": r["code_commune"], "commune": r["nom_commune"],
                "postcode": r["code_postal"] or None,
                "address": " ".join(filter(None, [r["adresse_numero"], r["adresse_nom_voie"]])) or None,
                "geom": func.ST_SetSRID(func.ST_MakePoint(float(lon), float(lat)), 4326) if lon and lat else None,
            }

    def upsert(self, records: list[dict[str, Any]]) -> int:
        if records:
            self.session.execute(insert(Sale).values(records).on_conflict_do_nothing(index_elements=["mutation_id"]))
        return len(records)

    def after_run(self) -> None:
        refresh_market_stats(self.session)

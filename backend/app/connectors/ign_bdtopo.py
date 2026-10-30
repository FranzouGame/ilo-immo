import json
from collections.abc import Iterable, Iterator
from typing import Any

from pyproj import Transformer
from sqlalchemy import text

from app.connectors.base import Connector
from app.http import PoliteClient

PAGE = 5000


class IgnBdtopoConnector(Connector):
    name = "ign_bdtopo"
    label = "IGN BD TOPO - bâtiments (emprise, hauteur, étages)"
    license = "Licence Ouverte 2.0 (IGN)"
    terms_url = "https://geoservices.ign.fr/bdtopo"
    update_frequency = "trimestrielle"
    warning = "Import lourd (~plusieurs centaines de milliers de bâtiments pour le 91). Utiliser `bbox` pour limiter."

    def fetch(self) -> Iterator[list[dict[str, Any]]]:
        w, s, e, n = self.cfg.get("bbox") or self.app_cfg["bbox"]
        tr = Transformer.from_crs(4326, 2154, always_xy=True)
        (x0, y0), (x1, y1) = tr.transform(w, s), tr.transform(e, n)
        step = float(self.cfg["tile_m"])
        http = PoliteClient(rate_per_s=2, timeout=300)
        x = x0
        while x < x1:
            y = y0
            while y < y1:
                start = 0
                while True:
                    feats = http.get_json(self.cfg["wfs_url"], params={
                        "SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": "BDTOPO_V3:batiment",
                        "OUTPUTFORMAT": "application/json", "SRSNAME": "EPSG:2154", "SORTBY": "cleabs",
                        "BBOX": f"{x},{y},{x + step},{y + step},EPSG:2154", "COUNT": PAGE, "STARTINDEX": start,
                    }).get("features", [])
                    if feats:
                        yield feats
                    if len(feats) < PAGE:
                        break
                    start += PAGE
                y += step
            x += step

    def normalize(self, raw: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for f in raw:
            p = f["properties"]
            yield {"ext_id": p.get("cleabs") or f["id"], "geom": json.dumps(f["geometry"]), "height": p.get("hauteur"),
                   "floors": p.get("nombre_d_etages"), "ground_alt": p.get("altitude_minimale_sol"),
                   "roof_alt": p.get("altitude_maximale_toit"), "usage": p.get("usage_1")}

    def upsert(self, records: list[dict[str, Any]]) -> int:
        if records:
            self.session.execute(text(
                "INSERT INTO building (ext_id, geom, height, floors, ground_alt, roof_alt, usage) VALUES "
                "(:ext_id, ST_Multi(ST_Force2D(ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(:geom),2154),4326))), "
                ":height, :floors, :ground_alt, :roof_alt, :usage) "
                "ON CONFLICT (ext_id) DO UPDATE SET geom=EXCLUDED.geom, height=EXCLUDED.height, floors=EXCLUDED.floors, "
                "ground_alt=EXCLUDED.ground_alt, roof_alt=EXCLUDED.roof_alt, usage=EXCLUDED.usage"), records)
        return len(records)

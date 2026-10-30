from collections.abc import Iterable, Iterator
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from app.connectors import overpass
from app.connectors.base import Connector
from app.models import Poi


class OsmConnector(Connector):
    name = "osm"
    label = "OpenStreetMap - parcs, forêts, eau, voies ferrées, grands axes"
    license = "ODbL 1.0 (© contributeurs OpenStreetMap) - attribution obligatoire"
    terms_url = "https://www.openstreetmap.org/copyright"
    update_frequency = "mensuelle"
    kinds = overpass.OSM_KINDS

    def fetch(self) -> Iterator[tuple[str, list[dict[str, Any]]]]:
        for kind, selectors, dept in ((k, s, d["code"]) for k, s in self.kinds.items() for d in self.app_cfg["departments"]):
            els = overpass.query(self.cfg["overpass_url"], dept, selectors)
            for i in range(0, len(els), self.batch_size):
                yield kind, els[i:i + self.batch_size]

    def normalize(self, raw: tuple[str, list[dict[str, Any]]]) -> Iterable[dict[str, Any]]:
        kind, els = raw
        for el in els:
            if (g := overpass.to_geometry(el)) is not None and not g.is_empty:
                yield {"osm_id": f"{el['type'][0]}{el['id']}", "kind": kind, "name": (el.get("tags") or {}).get("name"),
                       "geom": func.ST_SetSRID(func.ST_GeomFromText(g.wkt), 4326)}

    def upsert(self, records: list[dict[str, Any]]) -> int:
        if records:
            stmt = insert(Poi).values(records)
            self.session.execute(stmt.on_conflict_do_update(index_elements=["osm_id", "kind"], set_={"geom": stmt.excluded.geom, "name": stmt.excluded.name}))
        return len(records)

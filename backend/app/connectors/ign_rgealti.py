import math
from collections.abc import Iterable, Iterator
from typing import Any

from sqlalchemy import delete, func
from sqlalchemy.dialects.postgresql import insert

from app.connectors.base import Connector
from app.http import PoliteClient
from app.models import TerrainPoint

NO_DATA = -99999
_http: PoliteClient | None = None


def elevations(url: str, pts: list[tuple[float, float]]) -> list[float | None]:
    """Altitude (m) via le service altimétrique IGN (RGE ALTI). `None` si pas de donnée."""
    global _http
    _http = _http or PoliteClient(rate_per_s=5, timeout=60)
    r = _http.get_json(url, params={"lon": "|".join(f"{p[0]:.6f}" for p in pts), "lat": "|".join(f"{p[1]:.6f}" for p in pts),
                                    "resource": "ign_rge_alti_wld", "zonly": "true"})
    return [None if z == NO_DATA else float(z) for z in r["elevations"]]


class IgnRgealtiConnector(Connector):
    name = "ign_rgealti"
    label = "IGN RGE ALTI - modèle numérique de terrain (grille échantillonnée)"
    license = "Licence Ouverte 2.0 (IGN)"
    terms_url = "https://geoservices.ign.fr/rgealti"
    update_frequency = "annuelle"
    warning = "Échantillonne une grille (step_m) via le service d'altimétrie ; ne télécharge pas les dalles."

    def fetch(self) -> Iterator[list[tuple[float, float, float]]]:
        self.session.execute(delete(TerrainPoint))  # ré-échantillonnage complet
        self.session.commit()
        for w, s, e, n in self.bboxes():
            yield from self._grid(w, s, e, n)

    def _grid(self, w: float, s: float, e: float, n: float) -> Iterator[list[tuple[float, float, float]]]:
        step = float(self.cfg["step_m"])
        dlat = step / 110_540
        batch: list[tuple[float, float]] = []
        lat = s
        while lat < n:
            dlon = step / (111_320 * math.cos(math.radians(lat)))
            lon = w
            while lon < e:
                batch.append((lon, lat))
                if len(batch) == 100:
                    yield self._sample(batch)
                    batch = []
                lon += dlon
            lat += dlat
        if batch:
            yield self._sample(batch)

    def _sample(self, pts: list[tuple[float, float]]) -> list[tuple[float, float, float]]:
        return [(p[0], p[1], z) for p, z in zip(pts, elevations(self.cfg["url"], pts), strict=True) if z is not None]

    def normalize(self, raw: list[tuple[float, float, float]]) -> Iterable[dict[str, Any]]:
        for lon, lat, z in raw:
            yield {"geom": func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326), "alt": z}

    def upsert(self, records: list[dict[str, Any]]) -> int:
        if records:
            self.session.execute(insert(TerrainPoint).values(records))
        return len(records)

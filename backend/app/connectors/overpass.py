"""Aide Overpass (OpenStreetMap) partagée par les connecteurs `osm` et `transports`."""
from typing import Any

from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize, unary_union

from app.http import PoliteClient

# kind -> sélecteur Overpass
OSM_KINDS = {
    "park": ['way["leisure"="park"]', 'relation["leisure"="park"]'],
    "forest": ['way["landuse"="forest"]', 'relation["landuse"="forest"]', 'way["natural"="wood"]'],
    "water": ['way["natural"="water"]', 'relation["natural"="water"]', 'way["waterway"="river"]'],
    "railway": ['way["railway"="rail"]'],
    "road_major": ['way["highway"~"^(motorway|trunk|primary)$"]'],
    "industrial": ['way["landuse"="industrial"]'],
}
TRANSPORT_KINDS = {"station": ['node["railway"~"^(station|halt)$"]'], "stop": ['node["highway"="bus_stop"]']}


def query(url: str, dept: str, selectors: list[str], rate: float = 0.2) -> list[dict[str, Any]]:
    body = "".join(f"{s}(area.a);" for s in selectors)
    q = f'[out:json][timeout:900];area["ref:INSEE"="{dept}"]["boundary"="administrative"]->.a;({body});out geom;'
    return list(PoliteClient(rate_per_s=rate, timeout=1000).request("POST", url, data={"data": q}).json()["elements"])


def to_geometry(el: dict[str, Any]) -> BaseGeometry | None:
    if el["type"] == "node":
        return Point(el["lon"], el["lat"])
    if el["type"] == "way" and el.get("geometry"):
        pts = [(g["lon"], g["lat"]) for g in el["geometry"]]
        if len(pts) >= 4 and pts[0] == pts[-1]:
            return _poly(pts)
        return LineString(pts) if len(pts) >= 2 else None
    if el["type"] == "relation":
        lines = [LineString([(g["lon"], g["lat"]) for g in m["geometry"]])
                 for m in el.get("members", []) if m.get("role") == "outer" and len(m.get("geometry", [])) >= 2]
        polys = list(polygonize(unary_union(lines))) if lines else []
        return unary_union(polys) if polys else None
    return None


def _poly(pts: list[tuple[float, float]]) -> BaseGeometry:
    from shapely.geometry import Polygon
    p = Polygon(pts)
    return p if p.is_valid else p.buffer(0)

"""Calculs de vue, vis-à-vis, bruit : fonctions pures (testables sans base). Voir docs/calculs.md."""
import math
from dataclasses import dataclass
from typing import Any

from shapely import STRtree
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry

SECTORS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
Cfg = dict[str, Any]


@dataclass
class Obstacle:
    geom: BaseGeometry  # en mètres, repère local centré sur le bien
    roof_alt: float


@dataclass
class NearPoi:
    kind: str
    distance_m: float
    bearing_deg: float


def local_projector(lon0: float, lat0: float) -> Any:
    kx = 111_320.0 * math.cos(math.radians(lat0))
    ky = 110_540.0

    def project(x: Any, y: Any, z: Any = None) -> Any:
        return (x - lon0) * kx, (y - lat0) * ky

    return project


def bearing_deg(dx: float, dy: float) -> float:
    return math.degrees(math.atan2(dx, dy)) % 360


def analyze_view(obstacles: list[Obstacle], window_alt: float, cfg: Cfg) -> dict[str, Any]:
    """Lance des rayons autour du bien. Secteur = 45° ; premier bâtiment dont le toit dépasse la fenêtre."""
    radius = float(cfg["radius_m"])
    n_rays = int(cfg["rays_per_sector"])
    floor_h = float(cfg["floor_height_m"])
    tall = [o for o in obstacles if o.roof_alt > window_alt]
    tree = STRtree([o.geom for o in tall]) if tall else None
    origin = Point(0, 0)
    sectors: dict[str, dict[str, Any]] = {}
    angles: list[float] = []
    for i, name in enumerate(SECTORS):
        best: tuple[float, float] | None = None  # (distance, roof_alt)
        blocked = 0
        for k in range(n_rays):
            b = math.radians(i * 45 - 22.5 + (k + 0.5) * 45 / n_rays)
            ray = LineString([(0, 0), (radius * math.sin(b), radius * math.cos(b))])
            hit: tuple[float, float] | None = None
            if tree is not None:
                for idx in tree.query(ray, predicate="intersects"):
                    d = origin.distance(tall[int(idx)].geom.intersection(ray))
                    if hit is None or d < hit[0]:
                        hit = (d, tall[int(idx)].roof_alt)
            if hit is None:
                angles.append(0.0)
                continue
            blocked += 1
            angles.append(math.degrees(math.atan2(hit[1] - window_alt, max(hit[0], 1.0))))
            if best is None or hit[0] < best[0]:
                best = hit
        sectors[name] = {
            "distance_m": round(best[0]) if best else int(radius),
            "blocked_ratio": round(blocked / n_rays, 2),
            "open": best is None,
            "height_diff_m": round(best[1] - window_alt, 1) if best else 0.0,
            "floors_above": max(0, round((best[1] - window_alt) / floor_h)) if best else 0,
        }
    sky = 100 * (1 - (sum(angles) / len(angles)) / 90) if angles else 100.0
    return {"sectors": sectors, "sky_index": round(sky), "best_clearance_m": max(s["distance_m"] for s in sectors.values())}


def cone(orientation: str | None) -> list[str]:
    if orientation not in SECTORS:
        return []
    i = SECTORS.index(orientation)
    return [SECTORS[(i - 1) % 8], SECTORS[i], SECTORS[(i + 1) % 8]]


def _sector_risk(s: dict[str, Any], cfg: Cfg) -> float:
    if s["open"]:
        return 0.0
    proximity = max(0.0, 1 - s["distance_m"] / float(cfg["vis_a_vis_ref_distance_m"]))
    factor = 0.5 + 0.5 * min(1.0, max(0.0, s["height_diff_m"]) / (3 * float(cfg["floor_height_m"])))
    return float(100 * proximity * factor)


def vis_a_vis(sectors: dict[str, dict[str, Any]], orientation: str | None, cfg: Cfg) -> dict[str, Any]:
    risks = {n: _sector_risk(s, cfg) for n, s in sectors.items()}
    used = cone(orientation)
    if used:  # façade connue : pire risque dans le cône de vue
        name = max(used, key=lambda n: risks[n])
        note = f"façade {orientation}"
    else:  # inconnue : meilleur secteur
        name = min(risks, key=lambda n: risks[n])
        note = f"meilleur secteur ({name}), orientation inconnue"
    s = sectors[name]
    if s["open"] or risks[name] == 0:
        text = f"Aucun obstacle plus haut que la fenêtre à moins de {int(cfg['radius_m'])} m ({note})."
    else:
        above = f"{s['floors_above']} étage(s) plus haut" if s["floors_above"] else "toit juste au niveau de la fenêtre"
        text = f"Immeuble à {s['distance_m']} m ({name}), {above} (+{s['height_diff_m']} m) - {note}."
    return {"score": round(risks[name]), "sector": name, "explanation": text}


def view_quality(pois: list[NearPoi], sectors: dict[str, dict[str, Any]], orientation: str | None,
                 relief_m: float | None, cfg: Cfg) -> dict[str, Any]:
    used = cone(orientation)
    reasons: list[str] = []
    bonus = malus = 0.0
    seen: set[str] = set()
    for p in sorted(pois, key=lambda p: p.distance_m):
        sector = SECTORS[round(p.bearing_deg / 45) % 8]
        in_cone = (not used) or sector in used
        if p.kind in cfg["poi_weights"] and p.kind not in seen and p.distance_m <= cfg["green_radius_m"]:
            seen.add(p.kind)
            gain = cfg["poi_weights"][p.kind] * (1 - p.distance_m / cfg["green_radius_m"]) * (1 if in_cone else 0.5)
            bonus += gain
            reasons.append(f"+ {p.kind} à {round(p.distance_m)} m ({sector})")
        lim = {"road_major": cfg["road_distance_m"], "railway": cfg["rail_distance_m"],
               "industrial": cfg["industrial_distance_m"]}.get(p.kind)
        key = "!" + p.kind
        if lim and key not in seen and p.distance_m <= lim:
            seen.add(key)
            malus += {"road_major": 20, "railway": 20, "industrial": 15}[p.kind] * (1 - p.distance_m / lim)
            reasons.append(f"- {p.kind} à {round(p.distance_m)} m ({sector})")
    bonus = min(bonus, cfg["max_bonus"])
    malus = min(malus, cfg["max_malus"])
    pool = [sectors[n] for n in used if n in sectors] if used else list(sectors.values())
    if any(s["open"] for s in pool):
        bonus += 10
        reasons.append("+ ouverture dégagée jusqu'à la limite de calcul")
    if relief_m is not None and relief_m >= 5:
        bonus += 10 if relief_m >= 15 else 5
        reasons.append(f"+ situé {round(relief_m)} m au-dessus du terrain alentour")
    return {"score": round(max(0.0, min(100.0, 50 + bonus - malus))), "reasons": reasons}


def noise_score(pois: list[NearPoi], cfg: Cfg) -> int:
    total = 0.0
    for p in pois:
        lim = {"road_major": cfg["road_distance_m"], "railway": cfg["rail_distance_m"]}.get(p.kind)
        if lim and p.distance_m < lim:
            total += 60 * (1 - p.distance_m / lim)
    return round(min(100.0, total))


def dpe_rank(letter: str | None) -> int | None:
    return "ABCDEFG".index(letter) + 1 if letter and letter in "ABCDEFG" else None

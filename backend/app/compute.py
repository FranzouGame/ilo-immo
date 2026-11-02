"""Calcul des indicateurs d'un bien (PostGIS pour les requêtes, app.view pour les maths)."""
import math
from typing import Any

from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from shapely.ops import transform
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auction import auction_info
from app.config import app_config
from app.connectors.common import lonlat, point_sql
from app.market import comparable_ppm2, reference_ppm2
from app.models import Building, Poi, Property, Sale, TerrainPoint
from app.view import NearPoi, Obstacle, analyze_view, dpe_rank, local_projector, noise_score, view_quality, vis_a_vis

CONDITION_RANK = {"a_renover": 1, "bon": 2, "neuf": 3}
DEG = 0.005  # ~ 550 m en latitude : pré-filtre bbox, le filtrage exact est fait en Python


def _ground_altitude(session: Session, lon: float, lat: float, own: Building | None) -> float | None:
    if own is not None and own.ground_alt is not None:
        return own.ground_alt
    pt = point_sql(lon, lat)
    z = session.scalar(select(TerrainPoint.alt).order_by(TerrainPoint.geom.distance_centroid(pt)).limit(1))
    if z is not None:
        return float(z)
    cfg = app_config()["connectors"]["ign_rgealti"]
    from app.connectors.ign_rgealti import elevations  # import tardif : appel réseau de secours
    try:
        return elevations(cfg["url"], [(lon, lat)])[0]
    except Exception:
        return None


def _relief(session: Session, lon: float, lat: float, ground: float | None) -> float | None:
    if ground is None:
        return None
    pt = point_sql(lon, lat)
    avg = session.scalar(select(func.avg(TerrainPoint.alt)).where(func.ST_DWithin(TerrainPoint.geom, pt, 0.012)))
    return None if avg is None else ground - float(avg)


def _pois(session: Session, lon: float, lat: float) -> list[NearPoi]:
    pt = point_sql(lon, lat)
    rows = session.execute(
        select(Poi.kind, func.ST_Distance(func.geography(Poi.geom), func.geography(pt)),
               func.ST_Azimuth(pt, func.ST_ClosestPoint(Poi.geom, pt)))
        .where(func.ST_DWithin(Poi.geom, pt, 0.012), Poi.kind.not_in(["station", "stop"]))).all()
    return [NearPoi(k, float(d), math.degrees(a or 0.0)) for k, d, a in rows if d < 1500]


def _nearest_station(session: Session, lon: float, lat: float) -> float | None:
    pt = point_sql(lon, lat)
    d = session.scalar(select(func.ST_Distance(func.geography(Poi.geom), func.geography(pt)))
                       .where(Poi.kind == "station").order_by(Poi.geom.distance_centroid(pt)).limit(1))
    return None if d is None else float(d)


def compute_property(session: Session, prop: Property) -> dict[str, Any]:
    cfg = app_config()
    vcfg = cfg["view"]
    ll = lonlat(prop)
    keep = {k: v for k, v in (prop.computed or {}).items() if k in ("georisks",)}  # issus d'un connecteur
    out: dict[str, Any] = {**keep, "dpe_rank": dpe_rank(prop.dpe), "condition_rank": CONDITION_RANK.get(prop.condition or "")}
    out["score_price"] = prop.price
    if ll is None:
        return out
    lon, lat = ll
    if not prop.insee:  # biens importés sans code commune : on reprend celui de la vente DVF la plus proche
        prop.insee = session.scalar(select(Sale.insee).order_by(Sale.geom.distance_centroid(point_sql(lon, lat))).limit(1))
    proj = local_projector(lon, lat)
    pt = point_sql(lon, lat)
    # bâtiments voisins
    buildings = session.scalars(select(Building).where(func.ST_DWithin(Building.geom, pt, DEG))).all()
    shaped = [(b, transform(proj, to_shape(b.geom))) for b in buildings]
    origin = Point(0, 0)
    near = sorted(((g.distance(origin), b, g) for b, g in shaped), key=lambda t: t[0])
    own = near[0][1] if near and near[0][0] <= 15 else None
    ground = _ground_altitude(session, lon, lat, own)
    if own is not None and not prop.floors_total:
        out["floors_total_est"] = own.floors or (round(own.height / 3) if own.height else None)
    floors_total = prop.floors_total or out.get("floors_total_est")
    if prop.floor is not None and floors_total:
        out["relative_floor"] = round(min(1.0, prop.floor / floors_total), 2)
    out["ground_altitude_m"] = ground
    if ground is not None:
        floor_n = prop.floor if prop.floor is not None else 0
        window = ground + floor_n * vcfg["floor_height_m"] + (vcfg["eye_height_m"] if prop.floor is None else 0)
        out["window_altitude_m"] = round(window, 1)
        obstacles = []
        for _, b, g in near:
            if b is own:
                continue
            roof = b.roof_alt if b.roof_alt is not None else (
                (b.ground_alt if b.ground_alt is not None else ground) + (b.height or 0))
            obstacles.append(Obstacle(g, float(roof)))
        out["has_buildings"] = bool(buildings)  # sans BD TOPO : pas d'indicateur de vis-à-vis (score neutre, pas « 0 »)
        view = analyze_view(obstacles, window, vcfg) if buildings else {"sectors": {}}
        if buildings:
            out.update(view)
            out["vis_a_vis"] = vis_a_vis(view["sectors"], prop.orientation, vcfg)
        pois = _pois(session, lon, lat)
        out["view_quality"] = view_quality(pois, view["sectors"], prop.orientation, _relief(session, lon, lat, ground), vcfg)
        out["noise_score"] = noise_score(pois, vcfg)
        out["parks_count"] = sum(1 for p in pois if p.kind in ("park", "forest") and p.distance_m <= vcfg["green_radius_m"])
    if (st := _nearest_station(session, lon, lat)) is not None:
        out["station_walk_m"] = round(st * vcfg["walk_detour_factor"])
    out["score_price"] = prop.price
    if prop.price and prop.surface:
        ref = comparable_ppm2(session, lon, lat, prop.insee, prop.type, prop.surface) or reference_ppm2(session, lon, lat, prop.insee, prop.type)
        tags = prop.tags or []
        if "enchère" in tags:  # mise à prix ≠ prix de vente : on estime le prix final probable (voir app/auction.py)
            info = auction_info(prop.price, prop.surface, ref["median_ppm2"] if ref else None, (prop.insee or "")[:2],
                                cfg["knowledge"], (prop.custom or {}).get("occupation") == "occupé")
            out["auction"] = info
            out["score_price"] = info["estimate"]
            out["deal_pct"] = info.get("deal_pct")
        elif ref:
            out["market_ref"] = ref
            # viager : prix = valeur occupée, BRS : prix sans le terrain -> non comparables au marché libre
            if "viager" not in tags and (prop.custom or {}).get("dispositif") != "brs":
                ppm2 = prop.price / prop.surface
                out["market_ppm2"] = round(ppm2)
                out["market_gap_pct"] = round(100 * (ppm2 - ref["median_ppm2"]) / ref["median_ppm2"], 1)
                out["deal_pct"] = round(-out["market_gap_pct"])
    elif prop.price and "enchère" in (prop.tags or []):
        out["auction"] = auction_info(prop.price, None, None, (prop.insee or "")[:2], cfg["knowledge"], (prop.custom or {}).get("occupation") == "occupé")
        out["score_price"] = out["auction"]["estimate"]
    viager = (prop.custom or {}).get("viager")
    if isinstance(viager, dict) and viager.get("decote_pct"):
        out["deal_pct"] = viager["decote_pct"]  # décote d'occupation annoncée par l'agence
    return out


def recompute(session: Session, prop: Property) -> None:
    prop.computed = compute_property(session, prop)


def recompute_all(session: Session) -> int:
    n = 0
    for prop in session.scalars(select(Property)):
        recompute(session, prop)
        n += 1
    session.commit()
    return n



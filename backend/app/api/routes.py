import csv
import io
import uuid
from collections.abc import Callable
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from geoalchemy2.shape import from_shape
from pydantic import BaseModel, ConfigDict
from shapely.geometry import Point
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import alerts, auth
from app.compute import recompute
from app.config import app_config, settings
from app.connectors.ban import geocode
from app.connectors.dpe import lookup_dpe
from app.connectors.georisques import lookup_risks
from app.connectors.registry import is_enabled, load_all
from app.db import SessionLocal, get_session
from app.models import IngestionRun, MarketStat, Property, SavedFilter
from app.search import prop_dict, search

Db = Annotated[Session, Depends(get_session)]
public = APIRouter(prefix="/api")
router = APIRouter(prefix="/api", dependencies=[auth.Auth])


class Login(BaseModel):
    password: str


@public.post("/auth/login")
def login(body: Login) -> dict[str, str]:
    return {"token": auth.make_token(body.password)}


@public.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/config")
def get_config() -> dict[str, Any]:
    c = app_config()
    return {"department": c["department"], "department_name": c["department_name"], "map": c["map"],
            "criteria": c["scoring"]["criteria"], "presets": c["presets"], "view": c["view"]}


class PropertyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str | None = None
    title: str | None = None
    type: str | None = None
    price: float | None = None
    surface: float | None = None
    land_surface: float | None = None
    rooms: int | None = None
    floor: int | None = None
    floors_total: int | None = None
    balcony: bool | None = None
    elevator: bool | None = None
    orientation: str | None = None
    year_built: int | None = None
    address: str | None = None
    commune: str | None = None
    postcode: str | None = None
    insee: str | None = None
    dpe: str | None = None
    ges: str | None = None
    condition: str | None = None
    status: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    custom: dict[str, Any] | None = None
    manual_view: int | None = None
    manual_light: int | None = None
    manual_vis_a_vis: int | None = None
    lon: float | None = None
    lat: float | None = None


def _apply(p: Property, data: PropertyIn) -> None:
    vals = data.model_dump(exclude_unset=True)
    lon, lat = vals.pop("lon", None), vals.pop("lat", None)
    for k, v in vals.items():
        setattr(p, k, v)
    if lon is not None and lat is not None:
        p.geom = from_shape(Point(lon, lat), srid=4326)
    elif p.geom is None and p.address and not vals.get("lon"):
        g = geocode(app_config()["connectors"]["ban"]["url"], p.address, p.postcode)
        if g:
            p.geom = from_shape(Point(g["lon"], g["lat"]), srid=4326)
            p.postcode, p.insee, p.commune = p.postcode or g["postcode"], g["insee"], p.commune or g["city"]


@router.get("/listings")
def listings(db: Db, q: str | None = None, type: str | None = None, price_min: float | None = None, price_max: float | None = None,
             surface_min: float | None = None, rooms_min: int | None = None, floor_min: int | None = None,
             balcony: bool = False, elevator: bool = False, favorites: bool = False, hidden: bool = False,
             source: Annotated[list[str] | None, Query()] = None, sort: str = "recent", limit: int = 300) -> dict[str, Any]:
    """Recherche simple : filtres de base, sans score. Les champs inconnus sont exclus quand le filtre est actif."""
    stmt = select(Property)
    cond: list[Any] = [Property.status == "favori"] if favorites else ([] if hidden else [Property.status != "ecarte"])
    if q:
        like = f"%{q}%"
        cond.append(Property.title.ilike(like) | Property.commune.ilike(like) | Property.postcode.ilike(like) | Property.address.ilike(like))
    for col, op, val in ((Property.price, ">=", price_min), (Property.price, "<=", price_max), (Property.surface, ">=", surface_min),
                         (Property.rooms, ">=", rooms_min), (Property.floor, ">=", floor_min)):
        if val is not None:
            cond.append(col >= val if op == ">=" else col <= val)
    if type:
        cond.append(Property.type == type)
    if balcony:
        cond.append(Property.balcony.is_(True))
    if elevator:
        cond.append(Property.elevator.is_(True))
    if source:
        cond.append(Property.source.in_(source))
    order = {"price_asc": Property.price.asc().nulls_last(), "price_desc": Property.price.desc().nulls_last(),
             "ppm2": (Property.price / func.nullif(Property.surface, 0)).asc().nulls_last(),
             "surface": Property.surface.desc().nulls_last()}.get(sort, Property.created_at.desc())
    rows = db.scalars(stmt.where(*cond).order_by(order).limit(limit)).all()
    total = db.scalar(select(func.count()).select_from(Property).where(*cond)) or 0
    sources = sorted(db.scalars(select(Property.source).distinct()).all())
    return {"total": total, "items": [prop_dict(p) for p in rows], "sources": sources}


@router.post("/properties/search")
def search_properties(spec: dict[str, Any], db: Db) -> dict[str, Any]:
    items = search(db, spec)
    return {"total": len(items), "items": items}


@router.post("/properties/export")
def export_csv(spec: dict[str, Any], db: Db) -> Response:
    cols = ["score", "title", "type", "price", "surface", "price_m2", "rooms", "floor", "floors_total", "commune",
            "address", "dpe", "status", "url", "tags"]
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(cols)
    for r in search(db, spec):
        w.writerow([";".join(r[c]) if c == "tags" else r.get(c) for c in cols])
    return Response(buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="biens-{date.today()}.csv"'})


@router.post("/properties", status_code=201)
def create_property(data: PropertyIn, db: Db) -> dict[str, Any]:
    p = Property(source="manuel", tags=[], custom={}, photos=[], computed={})
    _apply(p, data)
    db.add(p)
    db.flush()
    recompute(db, p)
    db.commit()
    alerts.check_alerts(db)
    return prop_dict(p)


@router.post("/properties/prefill")
def prefill(body: dict[str, Any]) -> dict[str, Any]:
    """Colle une adresse -> coordonnées, DPE, risques, prix de secteur, indicateurs de vue (non enregistré)."""
    cfg = app_config()["connectors"]
    g = geocode(cfg["ban"]["url"], body["address"])
    if not g:
        raise HTTPException(404, "Adresse introuvable")
    p = Property(type=body.get("type", "appartement"), surface=body.get("surface"), price=body.get("price"),
                 floor=body.get("floor"), orientation=body.get("orientation"), insee=g["insee"], tags=[], computed={},
                 geom=from_shape(Point(g["lon"], g["lat"]), srid=4326))
    out: dict[str, Any] = {"address": g["label"], "lon": g["lon"], "lat": g["lat"], "postcode": g["postcode"],
                           "insee": g["insee"], "commune": g["city"]}
    calls: list[tuple[str, Callable[[], Any]]] = [
        ("dpe", lambda: lookup_dpe(cfg["dpe"]["url"], g["label"], p.surface)),
        ("georisks", lambda: lookup_risks(cfg["georisques"]["url"], g["lon"], g["lat"], cfg["georisques"]["radius_m"]))]
    for name, fn in calls:
        try:
            res = fn()
        except Exception as e:  # une source en panne ne doit pas bloquer la saisie
            out[f"{name}_error"] = str(e)[:200]
            continue
        if name == "dpe" and res:
            out.update({k: res[k] for k in ("dpe", "ges", "year_built")})
            p.dpe = res["dpe"]
        if name == "georisks":
            p.computed = {"georisks": res}
    with SessionLocal() as db:
        out["computed"] = _compute_transient(db, p)
    return out


def _compute_transient(db: Session, p: Property) -> dict[str, Any]:
    from app.compute import compute_property
    return compute_property(db, p)


def _get(db: Session, pid: int) -> Property:
    p = db.get(Property, pid)
    if p is None:
        raise HTTPException(404, "Bien introuvable")
    return p


@router.get("/properties/{pid}")
def get_property(pid: int, db: Db) -> dict[str, Any]:
    p = _get(db, pid)
    d = prop_dict(p)
    if d["lon"] is not None:
        rows = db.execute(text(
            "WITH pt AS (SELECT ST_SetSRID(ST_MakePoint(:lon,:lat),4326) g) "
            "SELECT sold_on, price, surface, price_m2, rooms, address, ST_Distance(CAST(sale.geom AS geography), CAST(pt.g AS geography)) AS dist, "
            "ST_X(sale.geom) lon, ST_Y(sale.geom) lat FROM sale, pt WHERE type=:t AND sale.geom IS NOT NULL "
            "AND ST_DWithin(sale.geom, pt.g, 0.008) ORDER BY dist LIMIT 15"),
            {"lon": d["lon"], "lat": d["lat"], "t": p.type}).mappings().all()
        d["neighbor_sales"] = [dict(r) for r in rows if r["dist"] <= 800]
    return d


@router.patch("/properties/{pid}")
def update_property(pid: int, data: PropertyIn, db: Db) -> dict[str, Any]:
    p = _get(db, pid)
    _apply(p, data)
    recompute(db, p)
    db.commit()
    return prop_dict(p)


@router.delete("/properties/{pid}", status_code=204)
def delete_property(pid: int, db: Db) -> None:
    db.delete(_get(db, pid))
    db.commit()


@router.post("/properties/{pid}/recompute")
def recompute_one(pid: int, db: Db) -> dict[str, Any]:
    p = _get(db, pid)
    recompute(db, p)
    db.commit()
    return prop_dict(p)


@router.post("/properties/{pid}/photos")
def add_photo(pid: int, db: Db, file: Annotated[UploadFile, File()]) -> dict[str, Any]:
    p = _get(db, pid)
    ext = (file.filename or "x.jpg").rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "webp"):
        raise HTTPException(400, "Format non supporté")
    name = f"{uuid.uuid4().hex}.{ext}"
    folder = settings().data_dir / "photos"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(file.file.read())
    p.photos = [*p.photos, name]
    db.commit()
    return prop_dict(p)


@router.get("/tags")
def tags(db: Db) -> list[str]:
    return sorted(db.scalars(select(func.unnest(Property.tags)).distinct()).all())


@router.get("/buildings")
def buildings(lon: float, lat: float, db: Db, radius: float = 300) -> dict[str, Any]:
    """Bâtiments autour d'un point (GeoJSON) pour l'extrusion 3D."""
    rows = db.execute(text(
        "SELECT ST_AsGeoJSON(geom) g, COALESCE(height, floors*3, 6) h, COALESCE(roof_alt - ground_alt, height, floors*3, 6) hh "
        "FROM building WHERE ST_DWithin(CAST(geom AS geography), CAST(ST_SetSRID(ST_MakePoint(:lon,:lat),4326) AS geography), :r) LIMIT 3000"),
        {"lon": lon, "lat": lat, "r": radius}).all()
    import json
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": json.loads(r.g), "properties": {"height": float(r.hh or r.h)}} for r in rows]}


class FilterIn(BaseModel):
    name: str
    spec: dict[str, Any]
    alert_min_score: float | None = None


@router.get("/filters")
def list_filters(db: Db) -> list[dict[str, Any]]:
    return [{"id": f.id, "name": f.name, "spec": f.spec, "alert_min_score": f.alert_min_score}
            for f in db.scalars(select(SavedFilter).order_by(SavedFilter.name))]


@router.post("/filters", status_code=201)
def save_filter(body: FilterIn, db: Db) -> dict[str, Any]:
    f = db.scalar(select(SavedFilter).where(SavedFilter.name == body.name)) or SavedFilter(name=body.name, alerted=[])
    f.spec, f.alert_min_score = body.spec, body.alert_min_score
    db.add(f)
    db.commit()
    return {"id": f.id}


@router.delete("/filters/{fid}", status_code=204)
def delete_filter(fid: int, db: Db) -> None:
    if f := db.get(SavedFilter, fid):
        db.delete(f)
        db.commit()


@router.get("/market/communes")
def market_communes(db: Db, type: str = "appartement") -> list[dict[str, Any]]:
    rows = db.scalars(select(MarketStat).where(MarketStat.scope == "commune", MarketStat.period == "all",
                                               MarketStat.type == type).order_by(MarketStat.label))
    return [{"insee": r.code, "commune": r.label, "median_ppm2": round(r.median_ppm2), "p25": round(r.p25_ppm2),
             "p75": round(r.p75_ppm2), "n": r.n} for r in rows]


@router.get("/market/series")
def market_series(insee: str, db: Db, type: str = "appartement") -> list[dict[str, Any]]:
    rows = db.scalars(select(MarketStat).where(MarketStat.scope == "commune", MarketStat.code == insee,
                                               MarketStat.type == type, MarketStat.period != "all").order_by(MarketStat.period))
    return [{"year": r.period, "median_ppm2": round(r.median_ppm2), "n": r.n} for r in rows]


@router.get("/connectors")
def list_connectors(db: Db) -> list[dict[str, Any]]:
    out = []
    for name, cls in load_all().items():
        last = db.scalar(select(IngestionRun).where(IngestionRun.source == name).order_by(IngestionRun.id.desc()).limit(1))
        out.append({"name": name, "label": cls.label, "license": cls.license, "terms_url": cls.terms_url,
                    "update_frequency": cls.update_frequency, "warning": cls.warning, "enabled": is_enabled(name),
                    "last_run": None if last is None else {"status": last.status, "n": last.n_records,
                                                           "at": last.started_at, "message": last.message[:300]}})
    return out


def _run_connector(name: str) -> None:
    from app.connectors.registry import build
    with SessionLocal() as s:
        build(name, s).run()


@router.post("/connectors/{name}/run", status_code=202)
def run_connector(name: str, bg: BackgroundTasks) -> dict[str, str]:
    if name not in load_all():
        raise HTTPException(404, "Connecteur inconnu")
    bg.add_task(_run_connector, name)
    return {"status": "started"}

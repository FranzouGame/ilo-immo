from datetime import date, datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _now() -> Any:
    return func.now()


class Property(Base):
    __tablename__ = "property"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(40), default="manuel")
    url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(200), default="")
    type: Mapped[str] = mapped_column(String(20), default="appartement")
    price: Mapped[float | None] = mapped_column(Float)
    surface: Mapped[float | None] = mapped_column(Float)
    land_surface: Mapped[float | None] = mapped_column(Float)
    rooms: Mapped[int | None] = mapped_column(SmallInteger)
    floor: Mapped[int | None] = mapped_column(SmallInteger)
    floors_total: Mapped[int | None] = mapped_column(SmallInteger)
    balcony: Mapped[bool | None]
    elevator: Mapped[bool | None]
    orientation: Mapped[str | None] = mapped_column(String(2))
    year_built: Mapped[int | None] = mapped_column(SmallInteger)
    address: Mapped[str | None] = mapped_column(Text)
    commune: Mapped[str | None] = mapped_column(String(80), index=True)
    postcode: Mapped[str | None] = mapped_column(String(5))
    insee: Mapped[str | None] = mapped_column(String(5), index=True)
    geom: Mapped[Any] = mapped_column(Geometry("POINT", 4326, spatial_index=True), nullable=True)
    dpe: Mapped[str | None] = mapped_column(String(1))
    ges: Mapped[str | None] = mapped_column(String(1))
    condition: Mapped[str | None] = mapped_column(String(12))  # a_renover | bon | neuf
    status: Mapped[str] = mapped_column(String(20), default="a_voir")
    notes: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    custom: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    manual_view: Mapped[int | None] = mapped_column(SmallInteger)    # 0-10
    manual_light: Mapped[int | None] = mapped_column(SmallInteger)   # 0-10
    manual_vis_a_vis: Mapped[int | None] = mapped_column(SmallInteger)  # 0-10 (10 = aucun vis-à-vis)
    photos: Mapped[list[str]] = mapped_column(JSONB, default=list)
    computed: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # dernière fois vue chez la source
    gone: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")  # retirée de la source
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now(), onupdate=_now())


class SourceRecord(Base):
    """Donnée brute d'origine (traçabilité)."""
    __tablename__ = "source_record"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(40), index=True)
    external_id: Mapped[str] = mapped_column(String(200))
    property_id: Mapped[int | None] = mapped_column(ForeignKey("property.id", ondelete="CASCADE"))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())
    __table_args__ = (Index("uq_source_record", "source", "external_id", "property_id", unique=True),)


class Sale(Base):
    """Vente DVF normalisée (une ligne par mutation)."""
    __tablename__ = "sale"
    id: Mapped[int] = mapped_column(primary_key=True)
    mutation_id: Mapped[str] = mapped_column(String(40), unique=True)
    sold_on: Mapped[date] = mapped_column(Date)
    price: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(20), index=True)
    surface: Mapped[float] = mapped_column(Float)
    rooms: Mapped[int | None] = mapped_column(SmallInteger)
    land_surface: Mapped[float | None] = mapped_column(Float)
    price_m2: Mapped[float] = mapped_column(Float)
    insee: Mapped[str] = mapped_column(String(5), index=True)
    commune: Mapped[str] = mapped_column(String(80))
    postcode: Mapped[str | None] = mapped_column(String(5))
    address: Mapped[str | None] = mapped_column(Text)
    geom: Mapped[Any] = mapped_column(Geometry("POINT", 4326, spatial_index=True), nullable=True)


class MarketStat(Base):
    __tablename__ = "market_stats"
    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(10))   # commune | cell (carré de 1 km, Lambert-93)
    code: Mapped[str] = mapped_column(String(40))
    label: Mapped[str] = mapped_column(String(80), default="")
    type: Mapped[str] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(8))   # 'all' ou 'YYYY'
    median_ppm2: Mapped[float] = mapped_column(Float)
    p25_ppm2: Mapped[float] = mapped_column(Float)
    p75_ppm2: Mapped[float] = mapped_column(Float)
    n: Mapped[int] = mapped_column(Integer)
    __table_args__ = (Index("uq_market", "scope", "code", "type", "period", unique=True),)


class SavedFilter(Base):
    __tablename__ = "saved_filter"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    spec: Mapped[dict[str, Any]] = mapped_column(JSONB)  # poids, plages, filtres durs
    alert_min_score: Mapped[float | None] = mapped_column(Float)
    alerted: Mapped[list[int]] = mapped_column(JSONB, default=list)


class Building(Base):
    __tablename__ = "building"
    id: Mapped[int] = mapped_column(primary_key=True)
    ext_id: Mapped[str] = mapped_column(String(40), unique=True)
    geom: Mapped[Any] = mapped_column(Geometry("MULTIPOLYGON", 4326, spatial_index=True))
    height: Mapped[float | None] = mapped_column(Float)
    floors: Mapped[int | None] = mapped_column(SmallInteger)
    ground_alt: Mapped[float | None] = mapped_column(Float)
    roof_alt: Mapped[float | None] = mapped_column(Float)
    usage: Mapped[str | None] = mapped_column(String(40))


class TerrainPoint(Base):
    __tablename__ = "terrain"
    id: Mapped[int] = mapped_column(primary_key=True)
    geom: Mapped[Any] = mapped_column(Geometry("POINT", 4326, spatial_index=True))
    alt: Mapped[float] = mapped_column(Float)


class Poi(Base):
    """Objets OSM : park, forest, water, railway, road_major, industrial, station, stop."""
    __tablename__ = "poi"
    id: Mapped[int] = mapped_column(primary_key=True)
    osm_id: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str | None] = mapped_column(String(120))
    geom: Mapped[Any] = mapped_column(Geometry("GEOMETRY", 4326, spatial_index=True))
    __table_args__ = (Index("uq_poi", "osm_id", "kind", unique=True),)


class ConstructionProject(Base):
    """Permis de construire (Sitadel)."""
    __tablename__ = "construction_project"
    id: Mapped[int] = mapped_column(primary_key=True)
    ext_id: Mapped[str] = mapped_column(String(40), unique=True)
    insee: Mapped[str] = mapped_column(String(5), index=True)
    kind: Mapped[str | None] = mapped_column(String(40))
    dwellings: Mapped[int | None] = mapped_column(Integer)
    authorized_on: Mapped[date | None] = mapped_column(Date)
    geom: Mapped[Any] = mapped_column(Geometry("POINT", 4326, spatial_index=True), nullable=True)


class IngestionRun(Base):
    __tablename__ = "ingestion_run"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(40), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(10), default="running")  # running|ok|error
    n_records: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")

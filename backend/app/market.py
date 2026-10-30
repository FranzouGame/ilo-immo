"""Statistiques de marché (DVF) : calcul agrégé et recherche du prix/m² de référence."""
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import MarketStat

CELL = "floor(ST_X(ST_Transform(geom,2154))/1000)::int || '_' || floor(ST_Y(ST_Transform(geom,2154))/1000)::int"
_AGG = """percentile_cont(0.5) WITHIN GROUP (ORDER BY price_m2), percentile_cont(0.25) WITHIN GROUP (ORDER BY price_m2),
 percentile_cont(0.75) WITHIN GROUP (ORDER BY price_m2), count(*)"""


def refresh_market_stats(session: Session) -> None:
    session.execute(text("DELETE FROM market_stats"))
    for scope, code, label, where in (("commune", "insee", "max(commune)", "true"), ("cell", CELL, "''", "geom IS NOT NULL")):
        for _, pexpr in (("all", "'all'"), ("year", "extract(year FROM sold_on)::text")):
            session.execute(text(
                f"INSERT INTO market_stats (scope, code, label, type, period, median_ppm2, p25_ppm2, p75_ppm2, n) "
                f"SELECT '{scope}', {code}, {label}, type, {pexpr}, {_AGG} FROM sale WHERE {where} "
                f"GROUP BY 2, 4, 5 HAVING count(*) >= 3"))
    session.commit()


def reference_ppm2(session: Session, lon: float | None, lat: float | None, insee: str | None,
                   type_: str, min_n: int = 10) -> dict[str, Any] | None:
    """Prix/m² médian de référence : carré de 1 km si assez de ventes, sinon commune."""
    if lon is not None and lat is not None:
        code = session.scalar(text(
            "SELECT floor(ST_X(t)/1000)::int || '_' || floor(ST_Y(t)/1000)::int FROM "
            "(SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon,:lat),4326),2154) t) s"), {"lon": lon, "lat": lat})
        row = session.scalar(select(MarketStat).where(MarketStat.scope == "cell", MarketStat.code == code,
                                                      MarketStat.type == type_, MarketStat.period == "all"))
        if row and row.n >= min_n:
            return {"scope": "cell", "median_ppm2": row.median_ppm2, "n": row.n}
    if insee:
        row = session.scalar(select(MarketStat).where(MarketStat.scope == "commune", MarketStat.code == insee,
                                                      MarketStat.type == type_, MarketStat.period == "all"))
        if row:
            return {"scope": "commune", "median_ppm2": row.median_ppm2, "n": row.n}
    return None

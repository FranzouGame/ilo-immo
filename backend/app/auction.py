"""Estimation du prix final d'une vente aux enchères judiciaire (fonction pure, chiffres dans config `knowledge`)."""
from typing import Any


def deposit(reserve: float, kn: dict[str, Any]) -> float:
    """Consignation exigée pour enchérir : 10 % de la mise à prix, 3 000 € minimum."""
    d = kn["auction_deposit"]
    return float(max(reserve * d["pct"] / 100, d["min_eur"]))


def multiple(reserve: float, kn: dict[str, Any]) -> float:
    for row in kn["auction_final_over_reserve"]:
        if row["max"] is None or reserve < row["max"]:
            return float(row["multiple"])
    return 1.0


def _bracket(reserve: float, kn: dict[str, Any]) -> dict[str, Any]:
    rows = kn["auction_paid_pct_by_reserve"]
    return next((r for r in rows if r["max"] is None or reserve < r["max"]), rows[-1])


def auction_info(reserve: float, surface: float | None, market_ppm2: float | None, dept: str | None,
                 kn: dict[str, Any], occupied: bool = False) -> dict[str, Any]:
    """Deux estimations indépendantes : (1) % du prix voisin selon la tranche de mise à prix, ajusté au département
    et à l'occupation, (2) multiple de la mise à prix. (1) est préférée quand le prix du secteur est connu.

    Ordres de grandeur statistiques, pas une prédiction : un bien occupé, en travaux ou très demandé peut sortir bien
    en dehors de la fourchette."""
    pct = kn["auction_price_pct_of_neighbors"]
    ratios = pct.get(dept or "", pct["default"])
    scale = ratios["median"] / pct["default"]["median"]  # ex. Essonne : 51 / 60
    b = _bracket(reserve, kn)
    occ = kn["auction_occupied_factor"] if occupied else 1.0
    paid = {k: round(b[k] * scale * occ) for k in ("q1", "median", "q3")}
    out: dict[str, Any] = {"reserve": reserve, "deposit": deposit(reserve, kn), "multiple": multiple(reserve, kn),
                           "surenchere_pct": kn["auction_surenchere_pct"], "ratios": ratios, "paid_pct": paid, "occupied": occupied}
    out["by_multiple"] = round(reserve * out["multiple"])
    if surface and market_ppm2:
        value = surface * market_ppm2
        out["market_value"] = round(value)
        out["reserve_pct_of_value"] = round(100 * reserve / value)
        out["by_market"] = {k: round(value * paid[k] / 100) for k in ("q1", "median", "q3")}
        out["estimate"] = out["by_market"]["median"]
        out["deal_pct"] = 100 - paid["median"]
    else:
        out["estimate"] = out["by_multiple"]
    return out

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


def auction_info(reserve: float, surface: float | None, market_ppm2: float | None, dept: str | None,
                 kn: dict[str, Any]) -> dict[str, Any]:
    """Deux estimations indépendantes : (1) % du prix voisin observé par département, (2) multiple de la mise à prix.

    L'estimation (1) est préférée quand le prix du secteur est connu. Ce sont des ordres de grandeur statistiques,
    pas une prédiction : un bien occupé, en travaux ou très demandé peut sortir bien en dehors de la fourchette."""
    ratios = kn["auction_price_pct_of_neighbors"].get(dept or "", kn["auction_price_pct_of_neighbors"]["default"])
    out: dict[str, Any] = {"reserve": reserve, "deposit": deposit(reserve, kn), "multiple": multiple(reserve, kn),
                           "surenchere_pct": kn["auction_surenchere_pct"], "ratios": ratios}
    out["by_multiple"] = round(reserve * out["multiple"])
    if surface and market_ppm2:
        base = surface * market_ppm2
        out["by_market"] = {k: round(base * ratios[k] / 100) for k in ("q1", "median", "q3")}
        out["estimate"] = out["by_market"]["median"]
    else:
        out["estimate"] = out["by_multiple"]
    return out

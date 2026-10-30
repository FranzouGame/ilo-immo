"""Score simplifié « Mes préférences » : 7 curseurs d'importance + 3 valeurs cibles -> spec pour scoring.evaluate."""
from typing import Any

GROUPS: dict[str, list[str]] = {
    "price": ["price"], "surface": ["surface"], "floor": ["floor", "relative_floor"],
    "view": ["view_quality", "vis_a_vis", "sky_view"], "station": ["station_distance"], "outdoor": ["balcony"], "deal": ["market_gap"],
}


def build_spec(cfg: dict[str, Any], weights: dict[str, int | None], budget: float | None, surface: float | None,
               floor: float | None) -> dict[str, Any]:
    """Les critères hors des 7 groupes sont mis à poids 0 ; les cibles chiffrées remplacent les plages par défaut."""
    d = cfg["scoring"]["simple"]
    w = {g: (weights.get(g) if weights.get(g) is not None else d["weights"][g]) for g in GROUPS}
    budget = budget if budget is not None else d["budget"]
    surface = surface if surface is not None else d["surface"]
    floor = floor if floor is not None else d["floor"]
    crit: dict[str, dict[str, Any]] = {c["key"]: {"weight": 0} for c in cfg["scoring"]["criteria"]}
    for g, keys in GROUPS.items():
        for k in keys:
            crit[k] = {"weight": w[g]}
    crit["price"].update(ideal=[None, budget], acceptable=[None, round(budget * 1.25)])
    crit["surface"].update(ideal=[surface, None], acceptable=[round(surface * 0.8), None])
    crit["floor"].update(ideal=[floor, None], acceptable=[max(0, floor - 2), None])
    return {"criteria": crit}

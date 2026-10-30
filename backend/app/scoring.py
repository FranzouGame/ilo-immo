"""Score pondéré 0-100 et filtres souples. Fonctions pures. Voir docs/calculs.md."""
from typing import Any

Spec = dict[str, Any]
Cfg_ = dict[str, Any]
MANUAL_FIELD = {"view": "manual_view", "light": "manual_light", "vis_a_vis": "manual_vis_a_vis"}


def get_field(data: dict[str, Any], path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def fit(v: float, ideal: list[float | None], acc: list[float | None]) -> float:
    """1 dans la plage idéale, décroît linéairement jusqu'à 0 au bord de la plage acceptable."""
    lo, hi = ideal
    alo, ahi = acc
    if lo is not None and v < lo:
        return 0.0 if alo is None or v <= alo else (v - alo) / (lo - alo)
    if hi is not None and v > hi:
        return 0.0 if ahi is None or v >= ahi else (ahi - v) / (ahi - hi)
    return 1.0


def merged_criteria(cfg: Cfg_, spec: Spec) -> list[dict[str, Any]]:
    """Config par défaut + surcharges utilisateur (weight, ideal, acceptable, prefer, hard)."""
    user = spec.get("criteria", {})
    out = []
    for c in cfg["scoring"]["criteria"]:
        m = {**c, **{k: v for k, v in user.get(c["key"], {}).items() if k != "hard"}}
        m["hard"] = user.get(c["key"], {}).get("hard")
        out.append(m)
    return out



def _criterion_score(c: dict[str, Any], prop: dict[str, Any], cfg: Cfg_) -> tuple[float | None, Any, bool]:
    """-> (score 0-1 ou None si pas de donnée, valeur brute, note_manuelle)."""
    manual = prop.get(MANUAL_FIELD.get(c.get("manual", ""), "")) if c.get("manual") else None
    if manual is not None:
        return float(manual) / 10, manual, True
    raw = get_field(prop, c["field"])
    if raw is None:
        return None, None, False
    if c["kind"] == "bool":
        return (1.0 if raw else 0.0), raw, False
    if c["kind"] == "set":
        prefer = c.get("prefer") or []
        vals = raw if isinstance(raw, list) else [raw]
        return (1.0 if any(v in prefer for v in vals) else 0.0), raw, False
    return fit(float(raw), c.get("ideal") or [None, None], c.get("acceptable") or [None, None]), raw, False


def _hard_check(c: dict[str, Any], raw: Any, widen: float) -> str:
    """-> 'ok' | 'near' (dans la marge d'élargissement) | 'fail'. Valeur inconnue = ok."""
    h = c.get("hard")
    if not h or raw is None:
        return "ok"
    if "any" in h:
        vals = raw if isinstance(raw, list) else [raw]
        return "ok" if any(v in h["any"] for v in vals) else "fail"
    if h.get("require"):
        return "ok" if raw else "fail"
    near = False
    for bound, sign in (("min", -1), ("max", 1)):
        b = h.get(bound)
        if b is None:
            continue
        ok = raw >= b if bound == "min" else raw <= b
        if not ok:
            slack = b + sign * widen * abs(b)
            if (raw >= slack) if bound == "min" else (raw <= slack):
                near = True
            else:
                return "fail"
    return "near" if near else "ok"


def evaluate(prop: dict[str, Any], spec: Spec, cfg: Cfg_) -> dict[str, Any]:
    sc = cfg["scoring"]
    widen = sc["widen_margin"] if spec.get("widen") else 0.0
    total = wsum = 0.0
    breakdown: list[dict[str, Any]] = []
    status = "ok"
    for c in merged_criteria(cfg, spec):
        score, raw, is_manual = _criterion_score(c, prop, cfg)
        check = _hard_check(c, raw, widen)
        if check == "fail":
            return {"passes": False, "score": 0, "near": False, "breakdown": []}
        if check == "near":
            status = "near"
        w = float(c.get("weight", 0)) * (sc["manual_weight_boost"] if is_manual else 1)
        if w <= 0:
            continue
        eff = sc["missing_value_score"] if score is None else score
        total += w * eff
        wsum += w
        breakdown.append({"key": c["key"], "label": c["label"], "weight": c.get("weight"), "value": raw,
                          "score": None if score is None else round(score, 2), "manual": is_manual})
    return {"passes": True, "near": status == "near", "score": round(100 * total / wsum) if wsum else 0,
            "breakdown": breakdown}


def matches_basic(prop: dict[str, Any], spec: Spec) -> bool:
    if spec.get("status") and prop["status"] not in spec["status"]:
        return False
    if spec.get("types") and prop["type"] not in spec["types"]:
        return False
    for k, v in (spec.get("custom") or {}).items():
        if str((prop.get("custom") or {}).get(k)) != str(v):
            return False
    if q := (spec.get("q") or "").strip().lower():
        hay = " ".join(str(prop.get(k) or "") for k in ("title", "address", "commune", "notes")) + " " + " ".join(prop.get("tags") or [])
        if q not in hay.lower():
            return False
    return True

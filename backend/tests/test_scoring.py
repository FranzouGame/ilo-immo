from app.scoring import evaluate, fit, matches_basic

CFG = {"scoring": {"missing_value_score": 0.5, "manual_weight_boost": 1.5, "widen_margin": 0.2, "criteria": [
    {"key": "floor", "label": "Étage", "kind": "range", "field": "floor", "ideal": [4, 8], "acceptable": [2, 12], "weight": 3},
    {"key": "view", "label": "Vue", "kind": "range", "field": "computed.view_quality.score", "manual": "view",
     "ideal": [65, None], "acceptable": [45, None], "weight": 2},
    {"key": "balcony", "label": "Balcon", "kind": "bool", "field": "balcony", "weight": 0},
]}}


def test_fit_trapezoid():
    assert fit(5, [4, 8], [2, 12]) == 1
    assert fit(3, [4, 8], [2, 12]) == 0.5
    assert fit(10, [4, 8], [2, 12]) == 0.5
    assert fit(1, [4, 8], [2, 12]) == 0


def test_missing_is_neutral_not_excluded():
    r = evaluate({"floor": None, "computed": {}}, {}, CFG)
    assert r["passes"] and r["score"] == 50


def test_manual_note_overrides_estimate():
    p = {"floor": 5, "computed": {"view_quality": {"score": 90}}, "manual_view": 2}
    assert evaluate(p, {}, CFG)["score"] < evaluate({**p, "manual_view": None}, {}, CFG)["score"]


def test_weights_and_hard_filters():
    p = {"floor": 5, "computed": {"view_quality": {"score": 10}}}
    only_floor = {"criteria": {"view": {"weight": 0}}}
    assert evaluate(p, only_floor, CFG)["score"] == 100
    hard = {"criteria": {"floor": {"hard": {"min": 6}}}}
    assert not evaluate(p, hard, CFG)["passes"]
    widened = evaluate(p, {**hard, "widen": True}, CFG)  # 5 >= 6 - 20% : « quasi éligible »
    assert widened["passes"] and widened["near"]


def test_basic_filters():
    p = {"status": "a_voir", "type": "appartement", "title": "T3 vue Seine", "address": "", "commune": "Evry", "notes": "",
         "tags": ["coup de cœur"], "custom": {"k": "v"}}
    assert matches_basic(p, {"q": "seine", "status": ["a_voir"], "custom": {"k": "v"}})
    assert not matches_basic(p, {"status": ["ecarte"]})

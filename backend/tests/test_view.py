from shapely.geometry import box

from app.view import NearPoi, Obstacle, analyze_view, noise_score, view_quality, vis_a_vis

CFG = {"radius_m": 300, "rays_per_sector": 7, "floor_height_m": 2.7, "vis_a_vis_ref_distance_m": 50, "green_radius_m": 800,
       "road_distance_m": 150, "rail_distance_m": 250, "industrial_distance_m": 300,
       "poi_weights": {"park": 12, "forest": 18, "water": 15}, "max_bonus": 35, "max_malus": 35}


def test_open_view():
    v = analyze_view([], 120, CFG)
    assert v["sky_index"] == 100 and v["best_clearance_m"] == 300
    assert vis_a_vis(v["sectors"], "S", CFG)["score"] == 0


def test_tall_building_north_blocks_north_only():
    wall = Obstacle(box(-40, 18, 40, 30), roof_alt=150)  # à 18 m au nord, plus haut que la fenêtre (120)
    v = analyze_view([wall], 120, CFG)
    assert v["sectors"]["N"]["distance_m"] == 18 and v["sectors"]["N"]["floors_above"] > 0
    assert v["sectors"]["S"]["open"]
    risk_n = vis_a_vis(v["sectors"], "N", CFG)
    assert risk_n["score"] > 50 and "18 m" in risk_n["explanation"]
    assert vis_a_vis(v["sectors"], None, CFG)["score"] == 0  # orientation inconnue : meilleur secteur
    assert v["sky_index"] < 100


def test_lower_building_does_not_block():
    low = Obstacle(box(-40, 18, 40, 30), roof_alt=100)
    assert analyze_view([low], 120, CFG)["sectors"]["N"]["open"]


def test_view_quality_and_noise():
    sectors = analyze_view([], 120, CFG)["sectors"]
    good = view_quality([NearPoi("forest", 100, 180)], sectors, "S", 20, CFG)
    bad = view_quality([NearPoi("road_major", 20, 180)], sectors, "S", None, CFG)
    assert good["score"] > 50 > bad["score"] - 10 and good["score"] > bad["score"]
    assert noise_score([NearPoi("road_major", 10, 0)], CFG) > 40


def test_view_quality_without_buildings_data():
    assert 0 <= view_quality([], {}, "SE", None, CFG)["score"] <= 100

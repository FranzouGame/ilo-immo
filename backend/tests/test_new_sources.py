import json

from app.auction import auction_info, deposit
from app.config import app_config
from app.connectors.programmes import parse_programme
from app.connectors.viager import ad_to_record, parse_state
from app.simple_score import build_spec

KN = app_config()["knowledge"]


def test_auction_deposit_and_estimates():
    assert deposit(70000, KN) == 7000 and deposit(10000, KN) == 3000
    info = auction_info(70000, 56, 3000, "91", KN)
    assert info["by_market"]["median"] == round(56 * 3000 * 0.51) and info["estimate"] == info["by_market"]["median"]
    assert info["multiple"] == 2.1 and info["by_multiple"] == 147000
    assert auction_info(70000, None, None, "91", KN)["estimate"] == 147000  # repli sur le multiple de la mise à prix


VIAGER = {"dossierId": 1, "urlPath": "/acheter/essonne-91/x/maison-4pieces-1", "bienTypeLabel": "maison", "venteTypeLabel": "Viager occupé",
          "bienNbPiece": 4, "bienSurfHabitable": 116, "bienCommunePostaleCp": "91700", "bienCommuneNccenr": "Fleury-Mérogis",
          "prixAchat": 173250, "mandatBouquetFai": 55000, "mandatRente": 755, "vlbDisplayed": 375000, "mandatDecotePercent": 54,
          "venteStatus": "à la vente", "image": "a.jpg", "tete1Age": "74", "tete1Sexe": "F"}


def test_viager_state_and_record():
    html = f'<script id="ng-state" type="application/json">{json.dumps({"k": {"b": {"data": VIAGER}}})}</script>'
    ads = parse_state(html)
    assert len(ads) == 1
    r = ad_to_record(ads[0], "https://s", "https://img")
    assert r and r["price"] == 173250 and r["custom"]["viager"]["rente"] == 755 and r["photos"][0].endswith("/a.jpg") and "viager" in r["tags"]
    assert ad_to_record({**VIAGER, "venteStatus": "vendu"}, "https://s", "https://img") is None
    assert ad_to_record({**VIAGER, "bienTypeLabel": "terrain"}, "https://s", "https://img") is None


def test_programme_parse():
    ld = {"@graph": [{"@type": "Product", "name": "Les Allées du Lac", "offers": {"lowPrice": "340000"}}]}
    html = (f'<script type="application/ld+json">{json.dumps(ld)}</script><h1>Les Allées du Lac</h1>'
            "<p>Avenue Kessel 78960 VOISINS LE BRETONNEUX Livraison : 1er trimestre 2023 Du 4 au 4 pièces à partir de 340 000€ "
            "appartement de 79,74 m² avec une terrasse de 9,65 m²</p>")
    url = "https://x/trouver-un-logement/ile-de-france/yvelines/voisins-le-bretonneux/tva-55/appartement/les-allees-du-lac"
    r = parse_programme(html, url)
    assert r and r["price"] == 340000 and r["postcode"] == "78960" and r["rooms"] == 4 and r["surface"] == 79.74
    assert r["balcony"] and r["custom"]["dispositif_label"] == "TVA 5,5 %" and r["custom"]["livraison"] == "1er trimestre 2023"


def test_simple_spec_targets_and_zero_weights():
    spec = build_spec(app_config(), {"price": 5}, 200000, 60, 4)["criteria"]
    assert spec["price"]["weight"] == 5 and spec["price"]["ideal"] == [None, 200000] and spec["surface"]["ideal"] == [60, None]
    assert spec["floor"]["ideal"] == [4, None] and spec["rooms"]["weight"] == 0 and spec["noise"]["weight"] == 0

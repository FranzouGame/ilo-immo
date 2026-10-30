import json

from app.connectors.interactives import parse_listing

LD = {"@graph": [{"@type": "RealEstateListing", "name": "Appartement en vente interactive à Morsang (91390)",
                  "offers": {"price": 109000}, "address": {"addressLocality": "Morsang", "postalCode": "91390"},
                  "numberOfRooms": 3, "floorSize": {"value": 46}, "image": ["https://x/1.webp"]}]}
HTML = f'<script type="application/ld+json">{json.dumps(LD)}</script><p>Situé au 2ème étage avec ascenseur et balcon</p>'
URL = "https://x/fr/annonce/ABC/appartement-morsang-91390-3p-46m2-109000euros.html"


def test_parse_listing():
    r = parse_listing(HTML, URL)
    assert r and r["price"] == 109000 and r["floor"] == 2 and r["elevator"] and r["balcony"] and r["photos"] == ["https://x/1.webp"]


def test_parse_listing_skips_land():
    assert parse_listing(HTML, URL.replace("appartement", "terrain-a-batir")) is None

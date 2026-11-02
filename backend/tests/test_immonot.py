from app.connectors.immonot import parse_card

CARD = """<li class="card-immo-li"><div id="card-1" class="card-immo"><img class="card-immo-img"
 alt="Maison a vendre Ballancourt-sur-Essonne 91610 Essonne 91 83 m2 4 pièces 232500 euros" src="https://cdn/x.webp">
<a href="/immobilier-notaire/detail/0000014933__w1/achat-maison-a-vendre-91610-ballancourt.html" id="0000014933__w1"
 title="Achat maison à Ballancourt-sur-Essonne (91610) - 232 500 €"></a>
<div class="card-immo-prix"><span>232 500 €</span></div>
<h2><div>Achat - maison </div><span>Ballancourt-sur-Essonne 91610</span></h2>
<p class="line-clamp-4">Maison construite en 1976, sur une parcelle de 223 m². Surface habitable de 83 m² sur 4 pièces, terrasse. Classe énergie : D</p></div></li>"""


def test_parse_card():
    r = parse_card(CARD, "https://www.immonot.com")
    assert r and r["price"] == 232500 and r["surface"] == 83 and r["rooms"] == 4 and r["land_surface"] == 223 and r["type"] == "maison"
    assert r["postcode"] == "91610" and r["commune"] == "Ballancourt-sur-Essonne" and r["balcony"] and r["year_built"] == 1976 and r["dpe"] == "D"
    assert r["url"].startswith("https://www.immonot.com/immobilier-notaire/detail/") and "notaire" in r["tags"]


def test_parse_card_skips_land():
    assert parse_card(CARD.replace("Achat - maison", "Achat - terrain"), "https://x") is None

from app.connectors.listings.encheres import parse_ad

HTML = """<div class="AdContent"><p class="Court">Tribunal Judiciaire d'Évry (Essonne)</p>
<p class="Date"><time datetime="2026-11-25T10:00:00">25 novembre</time></p>
<section class="AddressBlock"><div class="Lot"><div class="SousLot"><h2>Un appartement</h2>
<p><b>de 56,38 m²</b>, au 3ème étage, de trois pièces principales, <b>une terrasse</b></p></div>
<h3>Mise à prix : 70 000 €</h3></div>
<div class="Location"><p class="City">Palaiseau</p><p class="Street">1, allée du Clos</p>
<p class="Map"><a href="https://maps.google.fr/maps?q=48.7130775,2.2592363&z=13">plan</a></p></div></section></div>"""


def test_parse_ad():
    r = parse_ad(HTML, "https://x/annonce/1.html")
    assert r and r["type"] == "appartement" and r["price"] == 70000 and r["surface"] == 56.38
    assert r["rooms"] == 3 and r["balcony"] and r["commune"] == "Palaiseau" and r["lat"] == 48.7130775


def test_parse_ad_ignores_non_housing():
    assert parse_ad(HTML.replace("Un appartement", "Parts sociales de la SCI"), "u") is None

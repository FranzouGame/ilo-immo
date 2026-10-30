"""Logements neufs et aidés (TVA 5,5 %, BRS, PSLA, prix maîtrisé, vente HLM) : proprietairemaintenant.fr (plateforme des bailleurs)."""
import json
import re
from collections.abc import Iterable, Iterator
from typing import Any

from bs4 import BeautifulSoup

from app.connectors.ban import geocode
from app.connectors.base import ListingConnector
from app.scraping import RobotsClient

DISPOSITIFS = {"tva-55": "TVA 5,5 %", "brs": "BRS", "psla-location-accession": "PSLA", "accession-a-prix-maitrise": "Prix maîtrisé",
               "vente-hlm": "Vente HLM"}
URL_RE = re.compile(r"/ile-de-france/([^/]+)/([^/]+)/([^/]+)/(appartement|maison)/")


def parse_programme(html: str, url: str) -> dict[str, Any] | None:
    m = URL_RE.search(url)
    if not m:
        return None
    dept_slug, commune_slug, disp, typ = m.groups()
    s = BeautifulSoup(html, "html.parser")
    prod = None
    for tag in s.find_all("script", type="application/ld+json"):
        try:
            j = json.loads(tag.string or "{}")
        except ValueError:
            continue
        prod = next((n for n in j.get("@graph", [j]) if n.get("@type") == "Product"), None)
        if prod:
            break
    if not prod:
        return None
    price = (prod.get("offers") or {}).get("lowPrice")
    text = re.sub(r"\s+", " ", s.get_text(" ", strip=True))
    start = text.find("Fil d'Ariane")
    pc = re.search(r"\b(\d{5})\b", text[max(start, 0):])
    rooms = re.search(r"Du (\d) au (\d) pièces", text)
    liv = re.search(r"Livraison : (.+?) Du \d", text)
    surf = re.search(r"(\d+(?:[.,]\d+)?)\s*m²", text)
    photos = list(dict.fromkeys(u for u in re.findall(r'(?:src|data-src)="([^"]+/styles/programme/public/[^"]+)"', html)))[:8]
    img = prod.get("image")
    if isinstance(img, dict) and img.get("url") and not photos:
        photos = [img["url"]]
    low = text.lower()
    postcode = pc.group(1) if pc else None
    commune = commune_slug.replace("-", " ").title()  # remplacé par le nom officiel au géocodage
    label = DISPOSITIFS.get(disp, disp)
    return {
        "url": url, "title": prod.get("name", ""), "type": typ, "price": float(price) if price else None,
        "surface": float(surf.group(1).replace(",", ".")) if surf else None,
        "rooms": int(rooms.group(2)) if rooms else None,
        "balcony": True if ("balcon" in low or "terrasse" in low) else None, "elevator": True if "ascenseur" in low else None,
        "commune": commune, "postcode": postcode, "address": f"{commune} {postcode or ''}".strip(), "photos": photos,
        "tags": [label.lower()], "notes": f"Dispositif {label}. " + (f"Livraison : {liv.group(1)}." if liv else ""),
        "custom": {"dispositif": disp, "dispositif_label": label, "livraison": liv.group(1) if liv else None,
                   "pieces": f"{rooms.group(1)}-{rooms.group(2)}" if rooms else None, "prix_label": "à partir de",
                   "localisation": "approximative (centre commune)", "dept_slug": dept_slug},
        "raw": {"lowPrice": price},
    }


class ProgrammesConnector(ListingConnector):
    name = "programmes"
    label = "Neuf et accession aidée (proprietairemaintenant.fr)"
    terms_url = "https://www.proprietairemaintenant.fr"
    license = "Pages publiques (CGU du site à respecter)"
    update_frequency = "quotidienne"

    def fetch(self) -> Iterator[list[tuple[str, str]]]:
        http = RobotsClient(self.cfg["base_url"], self.cfg.get("delay_s", 3.0))
        sitemap = http.get_html(self.cfg["base_url"] + "/sitemap.xml")
        slugs = {d["slug"] for d in self.app_cfg["departments"]}
        urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", sitemap) if (m := URL_RE.search(u)) and m.group(1) in slugs]
        batch = [(u, http.get_html(u)) for u in urls]
        if batch:
            yield batch

    def normalize(self, raw: list[tuple[str, str]]) -> Iterable[dict[str, Any]]:
        ban = self.app_cfg["connectors"]["ban"]["url"]
        for u, h in raw:
            if rec := parse_programme(h, u):
                if rec["postcode"] and (g := geocode(ban, rec["address"], rec["postcode"])):
                    rec["lon"], rec["lat"], rec["insee"], rec["commune"] = g["lon"], g["lat"], g["insee"], g["city"]
                yield rec

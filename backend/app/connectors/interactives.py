"""Ventes interactives immobilières (36h-immo.com), département configuré. Pages publiques, JSON-LD schema.org."""
import json
import re
from collections.abc import Iterable, Iterator
from typing import Any

from bs4 import BeautifulSoup

from app.connectors.ban import geocode
from app.connectors.base import Connector
from app.connectors.common import upsert_properties
from app.scraping import RobotsClient


def parse_listing(html: str, url: str) -> dict[str, Any] | None:
    s = BeautifulSoup(html, "html.parser")
    node = None
    for tag in s.find_all("script", type="application/ld+json"):
        try:
            graph = json.loads(tag.string or "{}").get("@graph", [])
        except ValueError:
            continue
        node = next((n for n in graph if n.get("@type") == "RealEstateListing"), None)
        if node:
            break
    if not node:
        return None
    m = re.search(r"/(appartement|maison|propriete)-", url)
    if not m:
        return None  # terrains, murs commerciaux, immeubles… hors périmètre
    text = s.get_text(" ", strip=True).lower()
    addr = node.get("address", {})
    fl = re.search(r"(\d+)\s*(?:er|e|ème)\s+étage", text)
    dpe = re.search(r"\bdpe\b\s*:?\s*([a-g])\b", text)
    price = (node.get("offers") or {}).get("price")
    return {
        "url": url, "title": node.get("name", "").replace(" en vente interactive", ""),
        "type": "appartement" if m.group(1) == "appartement" else "maison", "price": float(price) if price else None,
        "surface": (node.get("floorSize") or {}).get("value"), "rooms": node.get("numberOfRooms"),
        "floor": int(fl.group(1)) if fl else (0 if "rez-de-chaussée" in text else None),
        "balcony": True if ("balcon" in text or "terrasse" in text) else None, "elevator": True if "ascenseur" in text else None,
        "dpe": dpe.group(1).upper() if dpe else None,
        "commune": addr.get("addressLocality"), "postcode": addr.get("postalCode"),
        "address": f"{addr.get('addressLocality')} {addr.get('postalCode')}",
        "photos": [u for u in node.get("image", [])][:8], "tags": ["vente interactive"],
        "notes": "Vente interactive : le prix affiché est le prix de départ, les offres montent en ligne.",
        "custom": {"localisation": "approximative (centre commune)"}, "raw": {"datePosted": node.get("datePosted")},
    }


class InteractivesConnector(Connector):
    name = "interactives"
    label = "Ventes interactives (36h-immo.com)"
    license = "Pages publiques (CGU du site à respecter)"
    terms_url = "https://www.36h-immo.com"
    update_frequency = "quotidienne"
    warning = "Collecte respectant robots.txt ; vérifier les CGU. Photos en lien direct vers le site source."

    def fetch(self) -> Iterator[list[tuple[str, str]]]:
        http = RobotsClient(self.cfg["base_url"], self.cfg.get("delay_s", 3.0))
        page = http.get_html(self.cfg["base_url"] + self.cfg["list_path"])
        urls = sorted({self.cfg["base_url"] + u for u in re.findall(r'/fr/annonce/\w+/[^"\']+\.html', page)})
        batch = [(u, http.get_html(u)) for u in urls]
        if batch:
            yield batch

    def normalize(self, raw: list[tuple[str, str]]) -> Iterable[dict[str, Any]]:
        out = []
        ban = self.app_cfg["connectors"]["ban"]["url"]
        for u, h in raw:
            if (r := parse_listing(h, u)) and (r["postcode"] or "").startswith(self.app_cfg["department"]):
                if g := geocode(ban, r["address"], r["postcode"]):
                    r["lon"], r["lat"], r["insee"] = g["lon"], g["lat"], g["insee"]
                out.append(r)
        return out

    def upsert(self, records: list[dict[str, Any]]) -> int:
        return upsert_properties(self.session, self.name, records)

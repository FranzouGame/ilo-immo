"""Annonces de notaires (Immonot.com, portail des études notariales) : pages de résultats publiques par département."""
import re
from collections.abc import Iterable, Iterator
from typing import Any

from bs4 import BeautifulSoup

from app.connectors.ban import geocode
from app.connectors.base import ListingConnector
from app.scraping import RobotsClient

TYPES = {"maison": "maison", "villa": "maison", "pavillon": "maison", "appartement": "appartement", "studio": "appartement", "duplex": "appartement"}
DPE_RE = re.compile(r"classe (?:énergie|energie|énergétique|energetique)?\s*:?\s*([a-g])\b|dpe\s*:?\s*([a-g])\b")


def detail_key(card: str) -> str | None:
    m = re.search(r"/immobilier-notaire/detail/([^/\"]+)/", card)
    return m.group(1) if m else None


def parse_card(card: str, base: str) -> dict[str, Any] | None:
    s = BeautifulSoup(card, "html.parser")
    a = s.select_one("a[href*='/immobilier-notaire/detail/']")
    if a is None:
        return None
    h2 = s.select_one("h2")
    kind = re.search(r"Achat\s*-\s*([a-zéè]+)", h2.get_text(" ", strip=True) if h2 else "", re.I)
    typ = TYPES.get(kind.group(1).lower()) if kind else None
    if typ is None:  # terrains, immeubles, locaux, parkings…
        return None
    place = s.select_one("h2 span")
    pc = re.search(r"(.+?)\s+(\d{5})\s*$", place.get_text(" ", strip=True)) if place else None
    price = s.select_one(".card-immo-prix")
    price_m = re.search(r"(\d[\d\s \xa0]*)\s*€", price.get_text(" ", strip=True)) if price else None
    desc_el = s.select_one("p.line-clamp-4")
    desc = desc_el.get_text(" ", strip=True) if desc_el else ""
    low = desc.lower()
    img = s.select_one("img.card-immo-img")
    alt = str(img.get("alt", "")) if img else ""
    surf = re.search(r"(\d+(?:[.,]\d+)?)\s*m2", alt) or re.search(r"surface habitable de (\d+(?:[.,]\d+)?)\s*m", desc)
    rooms = re.search(r"(\d+)\s*pi[èe]ces?", alt) or re.search(r"(\d+)\s*pi[èe]ces?", desc)
    land = re.search(r"parcelle de (\d+(?:[.,]\d+)?)\s*m", desc)
    floor = re.search(r"(\d+)\s*(?:er|e|ème)\s+étage", low)
    year = re.search(r"construite? en (\d{4})", low)
    dpe = DPE_RE.search(low)
    commune = pc.group(1) if pc else None
    return {
        "url": base + str(a["href"]), "title": str(a.get("title", "")).split(" - ")[0] or f"{typ.capitalize()} à {commune}", "type": typ,
        "price": float(re.sub(r"\D", "", price_m.group(1))) if price_m else None,
        "surface": float(surf.group(1).replace(",", ".")) if surf else None, "rooms": int(rooms.group(1)) if rooms else None,
        "land_surface": float(land.group(1).replace(",", ".")) if land else None, "floor": int(floor.group(1)) if floor else None,
        "balcony": True if ("balcon" in low or "terrasse" in low) else None, "elevator": True if "ascenseur" in low else None,
        "year_built": int(year.group(1)) if year else None, "dpe": (dpe.group(1) or dpe.group(2)).upper() if dpe else None,
        "commune": commune, "postcode": pc.group(2) if pc else None, "address": f"{commune} {pc.group(2)}" if pc else None,
        "photos": [str(img["src"])] if img and img.get("src") else [],
        "tags": ["notaire"], "notes": "Annonce d'une étude notariale. Vente classique : frais de notaire habituels.",
        "custom": {"localisation": "approximative (centre commune)"}, "raw": {"oid": a.get("id")},
    }


class ImmonotConnector(ListingConnector):
    name = "immonot"
    label = "Annonces de notaires (Immonot)"
    terms_url = "https://www.immonot.com"
    license = "Pages publiques (CGU du site à respecter)"
    update_frequency = "quotidienne"

    def fetch(self) -> Iterator[list[str]]:
        http = RobotsClient(self.cfg["base_url"], self.cfg.get("delay_s", 3.0))
        for d in self.app_cfg["departments"]:
            seen: set[str] = set()
            for page in range(1, int(self.cfg.get("max_pages", 40)) + 1):
                url = f"{self.cfg['base_url']}/immobilier-notaire/annonces/D{d['code']}/{d['slug']}.html" + (f"?page={page}" if page > 1 else "")
                cards = [str(c) for c in BeautifulSoup(http.get_html(url), "html.parser").select("li.card-immo-li")]
                keyed = [(k, c) for c in cards if (k := detail_key(c))]
                new = [c for k, c in keyed if k not in seen]
                if not new:
                    break
                seen |= {k for k, _ in keyed}
                yield new

    def normalize(self, raw: list[str]) -> Iterable[dict[str, Any]]:
        ban = self.app_cfg["connectors"]["ban"]["url"]
        for card in raw:
            if (rec := parse_card(card, self.cfg["base_url"])) and rec["postcode"]:
                if g := geocode(ban, rec["address"], rec["postcode"]):
                    rec["lon"], rec["lat"], rec["insee"] = g["lon"], g["lat"], g["insee"]
                yield rec

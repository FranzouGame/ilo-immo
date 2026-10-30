"""Ventes aux enchères judiciaires immobilières (Licitor), département configuré. Prix = mise à prix."""
import re
from collections.abc import Iterable, Iterator
from typing import Any

from bs4 import BeautifulSoup
from sqlalchemy import select

from app.connectors.base import ListingConnector
from app.models import Property
from app.scraping import RobotsClient

NUMS = {"une": 1, "un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8}
ORDINALS = {"premier": 1, "deuxième": 2, "troisième": 3, "quatrième": 4, "cinquième": 5, "sixième": 6, "septième": 7, "huitième": 8}


def parse_ad(html: str, url: str) -> dict[str, Any] | None:
    """Annonce Licitor -> dict `Property`. None si ce n'est pas un logement (parts de SCI, parking, terrain…)."""
    s = BeautifulSoup(html, "html.parser")
    lot = s.select_one(".SousLot")
    if lot is None or (h := lot.find("h2")) is None:
        return None
    kind = h.get_text(" ", strip=True).lower()
    if "appartement" in kind:
        typ = "appartement"
    elif any(k in kind for k in ("maison", "pavillon", "propriété bâtie", "villa")):
        typ = "maison"
    else:
        return None
    body = lot.get_text(" ", strip=True).lower()
    ad = s.select_one(".AdContent")
    text = ad.get_text(" ", strip=True) if ad else ""
    m_price = re.search(r"mise à prix\s*:\s*([\d\s \xa0]+)\s*€", text, re.I)
    m_surf = re.search(r"(\d+(?:[.,]\d+)?)\s*m²", body)
    m_rooms = re.search(r"(?:de\s+)?(\w+)\s+pièces?", body)
    floor = 0 if "rez-de-chaussée" in body else None
    if (m_fl := re.search(r"(?:au|du)\s+(\w+)\s+étage", body)):
        floor = ORDINALS.get(m_fl.group(1)) or (int(re.sub(r"\D", "", m_fl.group(1)) or 0) or None)
    city = s.select_one(".City")
    street = s.select_one(".Street")
    court = s.select_one(".Court")
    when = s.select_one(".Date time")
    ll = re.search(r"q=(-?\d+\.\d+),(-?\d+\.\d+)", str(s.select_one(".Map a") or ""))
    commune = city.get_text(" ", strip=True) if city else None
    return {
        "url": url, "title": f"Enchère - {kind.capitalize()} à {commune}", "type": typ,
        "price": float(re.sub(r"\D", "", m_price.group(1))) if m_price else None,
        "surface": float(m_surf.group(1).replace(",", ".")) if m_surf else None,
        "rooms": NUMS.get(m_rooms.group(1)) if m_rooms else None, "floor": floor,
        "balcony": True if ("balcon" in body or "terrasse" in body) else None,
        "address": ", ".join(x.get_text(" ", strip=True) for x in (street, city) if x) or None, "commune": commune,
        "tags": ["enchère"], "notes": "Prix = mise à prix (pas un prix de vente).",
        "custom": {"vente_le": when["datetime"] if when and when.has_attr("datetime") else None,
                   "tribunal": court.get_text(" ", strip=True) if court else None},
        "lon": float(ll.group(2)) if ll else None, "lat": float(ll.group(1)) if ll else None,
        "raw": {"html_len": len(html)},
    }


class EncheresConnector(ListingConnector):
    name = "encheres"
    label = "Enchères judiciaires immobilières (Licitor)"
    terms_url = "https://www.licitor.com"
    update_frequency = "quotidienne"
    base = "https://www.licitor.com"
    list_path = "/ventes-aux-encheres-immobilieres/{dept_slug}.html"

    def fetch(self) -> Iterator[list[tuple[str, str]]]:
        http = RobotsClient(self.base, self.cfg.get("delay_s", 3.0))
        known = set(self.session.scalars(select(Property.url).where(Property.source == self.name)))
        urls: list[str] = []
        for dept in self.app_cfg["departments"]:
            page = 1
            while page <= self.cfg.get("max_pages", 30):
                html = http.get_html(self.base + self.list_path.format(dept_slug=dept["slug"]) + f"?p={page}")
                found = re.findall(r'href="(/annonce/[^"]+\.html)"', html)
                new = [self.base + u for u in dict.fromkeys(found) if self.base + u not in urls]
                if not new:
                    break
                urls += new
                page += 1
        batch = []
        for u in urls:
            if u in known:
                continue  # shortcut: une annonce déjà connue n'est pas relue (modifs de dernière minute ignorées)
            batch.append((u, http.get_html(u)))
            if len(batch) == 10:
                yield batch
                batch = []
        if batch:
            yield batch

    def normalize(self, raw: list[tuple[str, str]]) -> Iterable[dict[str, Any]]:
        return [r for u, h in raw if (r := parse_ad(h, u))]

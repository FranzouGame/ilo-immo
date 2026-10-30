"""Annonces de viager (Renée Costes) : données structurées publiées dans la page (état Angular `ng-state`)."""
import json
import re
from collections.abc import Iterable, Iterator
from typing import Any

import httpx

from app.connectors.ban import geocode
from app.connectors.base import ListingConnector
from app.scraping import RobotsClient

TYPES = (("maison", "maison"), ("villa", "maison"), ("pavillon", "maison"), ("appart", "appartement"), ("studio", "appartement"))


def parse_state(html: str) -> list[dict[str, Any]]:
    m = re.search(r'<script[^>]*id="ng-state"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    out: list[dict[str, Any]] = []

    def walk(o: Any) -> None:
        if isinstance(o, dict):
            if "dossierId" in o and "urlPath" in o:
                out.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(json.loads(m.group(1)))
    return out


def ad_to_record(a: dict[str, Any], base: str, img_base: str) -> dict[str, Any] | None:
    label = str(a.get("bienTypeLabel") or "").lower()
    typ = next((t for k, t in TYPES if k in label), None)
    if typ is None or a.get("venteStatus") != "à la vente":
        return None
    price = a.get("prixAchat") or a.get("valeurOccupeeDisplayed") or a.get("vlbDisplayed")
    vente = str(a.get("venteTypeLabel") or "Viager")
    ages = [f"{'Femme' if a.get(f'tete{i}Sexe') == 'F' else 'Homme'} {a.get(f'tete{i}Age')} ans" for i in (1, 2) if a.get(f"tete{i}Age")]
    commune = a.get("bienCommuneNccenr") or a.get("bienCommuneLabel")
    return {
        "url": base + a["urlPath"], "title": f"{vente} - {typ.capitalize()} {a.get('bienNbPiece') or ''} p. à {commune}".replace("  ", " "),
        "type": typ, "price": float(price) if price else None, "surface": a.get("bienSurfHabitable"), "land_surface": a.get("bienSurfTerrain"),
        "rooms": a.get("bienNbPiece"), "floor": a.get("bienNbEtage"), "floors_total": a.get("bienTotalEtage"),
        "commune": commune, "postcode": a.get("bienCommunePostaleCp"), "address": f"{commune} {a.get('bienCommunePostaleCp')}",
        "photos": [f"{img_base}/resize/w/1024/h/0/img/{a['image']}"] if a.get("image") else [],
        "tags": ["viager", vente.lower()],
        "notes": "Viager : le prix affiché est la valeur « occupée » (bouquet + rente capitalisée). Voir le guide.",
        "custom": {"viager": {"type": vente, "bouquet": a.get("mandatBouquetFai"), "rente": a.get("mandatRente"),
                              "valeur_libre": a.get("vlbDisplayed"), "decote_pct": a.get("mandatDecotePercent"), "ages": ages},
                   "localisation": "approximative (centre commune)"},
        "raw": {"dossierId": a["dossierId"]},
    }


class ViagerConnector(ListingConnector):
    name = "viager"
    label = "Viager (Renée Costes)"
    terms_url = "https://www.costes-viager.com"
    license = "Pages publiques (CGU du site à respecter)"
    update_frequency = "quotidienne"

    def fetch(self) -> Iterator[list[dict[str, Any]]]:
        http = RobotsClient(self.cfg["base_url"], self.cfg.get("delay_s", 3.0))
        for d in self.app_cfg["departments"]:
            seen: set[int] = set()
            for page in range(1, int(self.cfg.get("max_pages", 15)) + 1):
                url = f"{self.cfg['base_url']}/acheter/annonces/departement/{d['slug']}-{d['code']}" + ("" if page == 1 else f"/{page}")
                try:
                    ads = parse_state(http.get_html(url))
                except httpx.HTTPStatusError:
                    break  # plus de page
                new = [a for a in ads if a["dossierId"] not in seen]
                if not new:
                    break
                seen |= {a["dossierId"] for a in new}
                yield new

    def normalize(self, raw: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        ban = self.app_cfg["connectors"]["ban"]["url"]
        for a in raw:
            if rec := ad_to_record(a, self.cfg["base_url"], self.cfg["img_base_url"]):
                if g := geocode(ban, rec["address"], rec["postcode"]):
                    rec["lon"], rec["lat"], rec["insee"] = g["lon"], g["lat"], g["insee"]
                yield rec

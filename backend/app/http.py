"""Client HTTP poli : limite de débit, reprise sur erreur (backoff), User-Agent explicite."""
import logging
import time
from typing import Any

import httpx

log = logging.getLogger("ilo.http")
UA = "ilo-recherche-immo/0.1 (usage personnel, donnees ouvertes)"


class PoliteClient:
    def __init__(self, rate_per_s: float = 5, retries: int = 4, timeout: float = 60) -> None:
        self.min_gap = 1 / rate_per_s
        self.retries = retries
        self._last = 0.0
        self.client = httpx.Client(timeout=timeout, headers={"User-Agent": UA}, follow_redirects=True)

    def request(self, method: str, url: str, **kw: Any) -> httpx.Response:
        for attempt in range(self.retries + 1):
            wait = self.min_gap - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                r = self.client.request(method, url, **kw)
                if r.status_code in (429, 500, 502, 503, 504) and attempt < self.retries:
                    delay = float(r.headers.get("Retry-After", 2 ** attempt))
                    log.warning("%s %s -> %s, retry dans %.0fs", method, url, r.status_code, delay)
                    time.sleep(min(delay, 60))
                    continue
                r.raise_for_status()
                return r
            except httpx.TransportError as e:
                if attempt == self.retries:
                    raise
                log.warning("erreur réseau %s, retry", e)
                time.sleep(2 ** attempt)
        raise RuntimeError("unreachable")

    def get_json(self, url: str, **kw: Any) -> Any:
        return self.request("GET", url, **kw).json()

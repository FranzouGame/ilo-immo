"""Client de collecte respectueux : robots.txt obligatoire, délai imposé, User-Agent explicite.

Ne contourne ni authentification, ni captcha, ni blocage. Un chemin interdit par robots.txt lève PermissionError.
Les conditions d'utilisation du site restent de la responsabilité de l'utilisateur (voir README).
"""
import urllib.robotparser
from urllib.parse import urlsplit

from app.http import UA, PoliteClient


class RobotsClient(PoliteClient):
    def __init__(self, base_url: str, min_delay_s: float = 3.0) -> None:
        super().__init__(rate_per_s=1 / min_delay_s)
        self.base = base_url.rstrip("/")
        self.robots = urllib.robotparser.RobotFileParser()
        self.robots.parse(self.request("GET", f"{self.base}/robots.txt").text.splitlines())
        if (d := self.robots.crawl_delay(UA)) is not None:
            self.min_gap = max(self.min_gap, float(d))

    def get_html(self, url: str) -> str:
        if not self.robots.can_fetch(UA, url):
            raise PermissionError(f"robots.txt interdit {urlsplit(url).path}")
        return self.request("GET", url).text

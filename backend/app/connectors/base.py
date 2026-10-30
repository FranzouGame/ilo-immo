"""Interface commune des connecteurs. Ajouter une source = ajouter un module ici (voir docs/connecteurs.md)."""
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from typing import Any, ClassVar

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import IngestionRun, Property

log = logging.getLogger("ilo.ingest")
REGISTRY: dict[str, type["Connector"]] = {}


class Connector(ABC):
    name: ClassVar[str]
    label: ClassVar[str]
    license: ClassVar[str]
    terms_url: ClassVar[str]
    update_frequency: ClassVar[str]
    warning: ClassVar[str] = ""          # avertissement juridique (connecteurs « biens à vendre »)
    batch_size: ClassVar[int] = 1000

    def __init_subclass__(cls, **kw: Any) -> None:
        super().__init_subclass__(**kw)
        if hasattr(cls, "name"):
            REGISTRY[cls.name] = cls

    def __init__(self, cfg: dict[str, Any], app_cfg: dict[str, Any], session: Session) -> None:
        self.cfg = cfg
        self.app_cfg = app_cfg
        self.session = session

    def bboxes(self) -> list[list[float]]:
        """Cadres à importer : option `bbox` du connecteur, sinon ceux des départements configurés."""
        return [self.cfg["bbox"]] if self.cfg.get("bbox") else [d["bbox"] for d in self.app_cfg["departments"]]

    @abstractmethod
    def fetch(self) -> Iterator[Any]:
        """Produit des lots bruts (le réseau et les fichiers sont lus ici)."""

    @abstractmethod
    def normalize(self, raw: Any) -> Iterable[dict[str, Any]]:
        """Brut -> enregistrements au schéma interne."""

    @abstractmethod
    def upsert(self, records: list[dict[str, Any]]) -> int:
        """Écrit en base (idempotent). Retourne le nombre d'enregistrements traités."""

    def after_run(self) -> None:  # noqa: B027
        """Hook optionnel (recalculs agrégés)."""

    def run(self) -> IngestionRun:
        run = IngestionRun(source=self.name)
        self.session.add(run)
        self.session.commit()
        try:
            for raw in self.fetch():
                run.n_records += self.upsert(list(self.normalize(raw)))
                self.session.commit()
            self.after_run()
            run.status = "ok"
        except Exception as e:  # journalisé puis remonté dans ingestion_run
            self.session.rollback()
            log.exception("ingestion %s en échec", self.name)
            run.status, run.message = "error", str(e)[:2000]
        run.finished_at = datetime.now(UTC)
        self.session.add(run)
        self.session.commit()
        log.info("ingestion %s: %s, %d enregistrements", self.name, run.status, run.n_records)
        return run


class ListingConnector(Connector, ABC):
    """Squelette « biens à vendre ». Désactivé par défaut.

    AVERTISSEMENT : avant toute implémentation, vérifier les conditions d'utilisation de la source,
    privilégier une API officielle ou un accord de partenariat, ne jamais contourner robots.txt/CGU.
    """
    license = "À vérifier avant usage"
    update_frequency = "selon la source"
    warning = "Vérifier CGU/licence ; privilégier API officielle ou partenariat ; pas de scraping sauvage."

    def fetch(self) -> Iterator[Any]:
        raise NotImplementedError(f"{self.name}: squelette non implémenté. {self.warning}")
        yield  # pragma: no cover

    def normalize(self, raw: Any) -> Iterable[dict[str, Any]]:
        """À implémenter : retourner des dicts compatibles `Property` (source=self.name, url, price, ...)."""
        return []

    def upsert(self, records: list[dict[str, Any]]) -> int:
        from app.connectors.common import upsert_properties
        return upsert_properties(self.session, self.name, records)

    def touch(self, urls: list[str]) -> None:
        """Marque des annonces connues comme « encore en ligne » sans les relire."""
        if urls:
            self.session.execute(update(Property).where(Property.source == self.name, Property.url.in_(urls))
                                 .values(last_seen_at=datetime.now(UTC)))
            self.session.commit()

    def run(self) -> IngestionRun:
        """Après un import réussi, les annonces non revues sont marquées `gone` (retirées de la source)."""
        start = datetime.now(UTC)
        run = super().run()
        if run.status == "ok":
            seen = self.session.scalar(select(func.count()).select_from(Property)
                                       .where(Property.source == self.name, Property.last_seen_at >= start)) or 0
            if seen:  # garde-fou : une source muette ne doit pas tout faire disparaître
                self.session.execute(update(Property).where(Property.source == self.name)
                                     .values(gone=Property.last_seen_at.is_(None) | (Property.last_seen_at < start)))
                self.session.commit()
        return run

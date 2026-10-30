"""Conteneur worker : ingestions périodiques (APScheduler), recalculs et alertes."""
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.alerts import check_alerts
from app.compute import recompute_all
from app.config import app_config
from app.connectors.registry import build, is_enabled, load_all
from app.db import SessionLocal

log = logging.getLogger("ilo.worker")
DERIVED = {"dvf", "dpe", "georisques", "ban", "osm", "transports", "ign_bdtopo", "ign_rgealti"}


def ingest(name: str) -> None:
    with SessionLocal() as s:
        build(name, s).run()
    if name in DERIVED:
        with SessionLocal() as s:
            log.info("recalcul de %d biens", recompute_all(s))


def alerts_job() -> None:
    with SessionLocal() as s:
        check_alerts(s)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = app_config()
    sched = BlockingScheduler(timezone="Europe/Paris")
    for name in load_all():
        c = cfg["connectors"].get(name, {})
        if is_enabled(name) and c.get("schedule"):
            sched.add_job(ingest, CronTrigger.from_crontab(c["schedule"]), args=[name], id=name, max_instances=1, coalesce=True)
            log.info("planifié: %s (%s)", name, c["schedule"])
    sched.add_job(alerts_job, CronTrigger.from_crontab(cfg["alerts"]["check_schedule"]), id="alerts")
    sched.start()


if __name__ == "__main__":
    main()

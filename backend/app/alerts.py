"""Alertes : un nouveau bien dépassant le score d'un filtre enregistré -> e-mail (si SMTP) sinon fichier."""
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import app_config, settings
from app.models import SavedFilter
from app.search import search


def _notify(subject: str, body: str) -> None:
    s = settings()
    if s.smtp_host and s.alert_email_to:
        msg = EmailMessage()
        msg["Subject"], msg["From"], msg["To"] = subject, s.alert_email_from or s.smtp_user, s.alert_email_to
        msg.set_content(body)
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            if s.smtp_user:
                smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(msg)
    path = s.data_dir / app_config()["alerts"]["file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(UTC).isoformat(timespec='seconds')}] {subject}\n{body}\n\n")


def check_alerts(session: Session) -> int:
    sent = 0
    for f in session.scalars(select(SavedFilter).where(SavedFilter.alert_min_score.is_not(None))):
        hits = [r for r in search(session, f.spec) if r["score"] >= (f.alert_min_score or 0) and r["id"] not in f.alerted]
        for r in hits:
            _notify(f"[ilo] {f.name} : {r['title'] or r['address']} ({r['score']}/100)",
                    f"{r['commune']} - {r['price']} € - {r['surface']} m² - {r['url'] or 'saisie manuelle'}")
            sent += 1
        if hits:
            f.alerted = [*f.alerted, *(r["id"] for r in hits)]
    session.commit()
    return sent

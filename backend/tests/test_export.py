from app.config import Settings, db_url
from app.export_static import PRIVATE_KEYS


def test_private_keys_declared():
    assert {"notes", "status"} <= set(PRIVATE_KEYS)


def test_db_url_accepts_special_characters_in_password():
    s = Settings(database_url="", postgres_user="ilo", postgres_password="p@ss:w/rd#1", postgres_host="db", postgres_db="ilo")
    u = db_url(s)
    assert u.host == "db" and u.password == "p@ss:w/rd#1" and u.username == "ilo"


def test_merge_history_keeps_old_price_on_change():
    from app.export_static import merge_history
    prev = {"price": 100000, "price_history": [{"date": "2026-10-01", "price": 120000}]}
    assert merge_history(prev, 100000, "2026-11-02") == [{"date": "2026-10-01", "price": 120000}]
    assert merge_history(prev, 90000, "2026-11-02")[-1] == {"date": "2026-11-02", "price": 100000}
    assert merge_history(None, 90000, "2026-11-02") == []


def test_feed_lists_new_and_price_drops():
    from datetime import UTC, datetime

    from app.export_static import feed_xml
    now = datetime(2026, 11, 2, tzinfo=UTC)
    new = {"created_at": "2026-11-01T10:00:00+00:00", "title": "T3 Évry", "commune": "Évry", "price": 150000, "url": "https://x/1", "price_history": []}
    drop = {"created_at": "2026-05-01T10:00:00+00:00", "title": "Maison", "commune": "Massy", "price": 90000, "url": "https://x/2",
            "price_history": [{"date": "2026-11-01", "price": 100000}]}
    old = {"created_at": "2026-05-01T10:00:00+00:00", "title": "Vieux", "commune": "X", "price": 1, "url": "https://x/3", "price_history": []}
    xml = feed_xml([new, drop, old], "https://site/", now)
    assert "Nouveau : T3 Évry" in xml and "Prix ↓ 10 %" in xml and "Vieux" not in xml

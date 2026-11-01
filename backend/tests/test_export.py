from app.config import Settings, db_url
from app.export_static import PRIVATE_KEYS


def test_private_keys_declared():
    assert {"notes", "status"} <= set(PRIVATE_KEYS)


def test_db_url_accepts_special_characters_in_password():
    s = Settings(database_url="", postgres_user="ilo", postgres_password="p@ss:w/rd#1", postgres_host="db", postgres_db="ilo")
    u = db_url(s)
    assert u.host == "db" and u.password == "p@ss:w/rd#1" and u.username == "ilo"

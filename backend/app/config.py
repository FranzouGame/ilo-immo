"""Réglages : variables d'environnement (secrets, URLs) + YAML (métier)."""
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""  # optionnel ; sinon construit depuis POSTGRES_* (mots de passe avec @, :, / acceptés)
    postgres_user: str = "ilo"
    postgres_password: str = "ilo"
    postgres_db: str = "ilo"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    auth_enabled: bool = True
    app_password: str = ""
    secret_key: str = "dev-insecure"
    config_path: Path = Path("config/app.yaml")
    data_dir: Path = Path("data")
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_email_from: str = ""
    alert_email_to: str = ""


def db_url(s: Settings) -> URL:
    if s.database_url:
        return make_url(s.database_url)
    return URL.create("postgresql+psycopg", s.postgres_user, s.postgres_password, s.postgres_host, s.postgres_port, s.postgres_db)


@lru_cache
def settings() -> Settings:
    return Settings()


@lru_cache
def app_config() -> dict[str, Any]:
    cfg: dict[str, Any] = yaml.safe_load(settings().config_path.read_text(encoding="utf-8"))
    if only := os.environ.get("DEPARTMENTS"):  # ex. DEPARTMENTS=91 pour restreindre
        cfg["departments"] = [d for d in cfg["departments"] if d["code"] in only.split(",")]
    return cfg


def departments() -> list[dict[str, Any]]:
    return list(app_config()["departments"])

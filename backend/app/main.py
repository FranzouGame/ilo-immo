import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import public, router
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = FastAPI(title="ilo - recherche immobilière Essonne")
app.include_router(public)
app.include_router(router)
_photos = settings().data_dir / "photos"
_photos.mkdir(parents=True, exist_ok=True)
app.mount("/api/photos", StaticFiles(directory=_photos), name="photos")  # noms aléatoires non devinables

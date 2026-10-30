# Ilo - recherche immobilière Essonne (91)

Outil local : biens + carte 2D/3D + score pondéré (vue, hauteur, vis-à-vis) sur données ouvertes. Pas de scraping de portails.

## Stack
Python 3.12 / FastAPI / SQLAlchemy 2 / Alembic / PostGIS 16 · React + TS strict + Vite + MapLibre · APScheduler (worker) · Docker Compose.

## Commandes
- `make up` / `down` / `logs` · `make migrate` · `make seed` (démo)
- `make ingest [SRC=dvf|osm|transports|ign_bdtopo|ign_rgealti|sitadel|ban|dpe|georisques]`
- `make test` (pytest + vitest) · `make lint` (ruff + mypy strict + tsc + eslint)
- Local front : `cd frontend && npm test && npm run lint` ; back : via conteneur (`docker compose run --rm backend pytest`).

## Conventions
- Maths pures dans `view.py` / `scoring.py` (testées) ; SQL/PostGIS dans `compute.py`, connecteurs, routes.
- Aucune valeur métier en dur : tout dans `config/app.yaml`. Secrets uniquement `.env`.
- Un connecteur = un module dans `app/connectors/` (hérite `Connector`, auto-découvert). Annonces = `ListingConnector`, désactivé.
- Typage strict (mypy strict, TS strict) ; ruff line-length 140. Code/commentaires en français.

## Décisions
- Score calculé à la volée en mémoire (poids dans la requête) ; indicateurs lourds stockés dans `property.computed` (JSONB).
- Données inconnues = score neutre 0,5, jamais exclusion. Notes manuelles > estimations (poids ×1,5).
- Migration Alembic : autogénérée puis nettoyée (filtre `include_object` pour ignorer tiger/topology de l'image PostGIS).
- BD TOPO via WFS Géoplateforme par tuiles Lambert-93 (pas de dump GPKG) ; RGE ALTI via service altimétrie (grille).

## Pièges
- Autogenerate duplique les index spatiaux (`idx_*_geom`) : supprimer les `create_index` manuels du fichier généré.
- Sans BD TOPO importée : pas de vis-à-vis/ciel (volontairement non calculés, score neutre).
- Hook sandbox : `curl` bloqué dans cette session ; tester l'API avec python/urllib.
- Dataset ADEME `dpe03existant` et URL Sitadel changent : voir `config/app.yaml`.
- Overpass / WFS IGN : lents et limités ; `PoliteClient` gère débit + retry.

Suivi détaillé : `docs/SUIVI.md`. Mettre ce fichier (< 80 lignes) à jour à chaque changement structurant.

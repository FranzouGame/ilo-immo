# Ilo - recherche immobilière Essonne (91)

Site d'annonces local (Essonne) : offres absentes des grands portails (enchères, ventes interactives, saisie manuelle), filtres simples.
Moteur de score/vue/vis-à-vis conservé côté API mais plus exposé dans l'UI. Collecte via `app/scraping.py` (robots.txt obligatoire).

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
- UI = `/api/listings` (filtres SQL simples). `/api/properties/search` (score) reste pour usage avancé. Sources actives : encheres, interactives, programmes, viager. Score = `app/simple_score.py` (7 groupes) + `scoring.evaluate`.
- Un connecteur d'annonces ne doit jamais écraser tags/notes/custom/photos/status (`USER_OWNED` dans `connectors/common.py`).
- Score calculé à la volée en mémoire (poids dans la requête) ; indicateurs lourds stockés dans `property.computed` (JSONB).
- Données inconnues = score neutre 0,5, jamais exclusion. Notes manuelles > estimations (poids ×1,5).
- Migration Alembic : autogénérée puis nettoyée (filtre `include_object` pour ignorer tiger/topology de l'image PostGIS).
- BD TOPO via WFS Géoplateforme par tuiles Lambert-93 (pas de dump GPKG) ; RGE ALTI via service altimétrie (grille).

- Enchères : prix noté = estimation `computed.score_price` (`app/auction.py`, chiffres `knowledge:` du YAML, source data.gouv MdB Scanner). Viager : prix = valeur occupée, pas de market_gap.
- Annonces disparues : `last_seen_at`/`gone` (ListingConnector.run) ; ne jamais marquer gone si aucune annonce revue.

## Pièges
- Autogenerate duplique les index spatiaux (`idx_*_geom`) : supprimer les `create_index` manuels du fichier généré.
- Sans BD TOPO importée : pas de vis-à-vis/ciel (volontairement non calculés, score neutre).
- Si `/api/listings` renvoie 404 depuis l'hôte alors que le code est bon : vieux conteneur/daemon (Docker Desktop vs WSL) sur le port 8000 ; `docker compose up -d --build`.
- Hook sandbox : `curl` bloqué dans cette session ; tester l'API avec python/urllib.
- Dataset ADEME `dpe03existant` et URL Sitadel changent : voir `config/app.yaml`.
- Overpass / WFS IGN : lents et limités ; `PoliteClient` gère débit + retry.

Suivi détaillé : `docs/SUIVI.md`. Mettre ce fichier (< 80 lignes) à jour à chaque changement structurant.

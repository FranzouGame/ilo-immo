# Architecture

```
 Navigateur ── nginx (frontend, :8080) ──/api──▶ FastAPI (backend, :8000) ──▶ PostgreSQL + PostGIS
 React + MapLibre                                   │  scoring / view / compute                ▲
                                                    └─ connecteurs (lookup à la demande)       │
                              Worker (APScheduler) ── connecteurs.run() planifiés ──────────────┘
```

- `backend/app/view.py`, `scoring.py` : fonctions **pures** (testables sans base).
- `backend/app/compute.py` : requêtes PostGIS (bâtiments, POI, relief, DVF) puis appel des fonctions pures ; résultat dans `property.computed` (JSONB).
- `backend/app/search.py` : charge les biens, applique filtres souples + score à la volée (poids fournis par la requête).
- `backend/app/connectors/` : un module par source, découverte automatique (`registry.py`), journal dans `ingestion_run`.
- Tables : `property`, `source_record` (brut), `sale` (DVF), `market_stats`, `saved_filter`, `building`, `terrain`, `poi`, `construction_project`, `ingestion_run`.
- Config métier : `config/app.yaml` (département, seuils, pondérations par défaut, connecteurs, planning). Secrets : `.env`.
- Auth : mot de passe unique (`APP_PASSWORD`) → JWT 7 jours ; `AUTH_ENABLED=false` pour désactiver en local.

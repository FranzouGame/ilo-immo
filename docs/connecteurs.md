# Connecteurs

Contrat (`backend/app/connectors/base.py`) : attributs `name`, `label`, `license`, `terms_url`, `update_frequency` ;
méthodes `fetch()` (itère des lots bruts), `normalize(lot)`, `upsert(records)` (idempotent), `after_run()` optionnel.
`run()` journalise dans `ingestion_run` (statut, volume, erreur) et ne laisse jamais une source en panne bloquer les autres.

## Ajouter une source
1. Créer `backend/app/connectors/ma_source.py` avec une classe héritant de `Connector` (découverte automatique, aucune autre modification de code).
2. Ajouter un bloc `connectors.ma_source` dans `config/app.yaml` (`enabled`, `schedule` cron, options).
3. `make ingest SRC=ma_source`. Utiliser `PoliteClient` (`app/http.py`) : débit limité, reprise sur 429/5xx.
4. Source d'annonces : hériter de `ListingConnector` (désactivée par défaut). **Vérifier CGU/licence avant** ; API officielle ou accord de partenariat d'abord.

## Mettre à jour les données
- Automatique : worker, selon `schedule`. Manuel : `make ingest [SRC=nom]` (recalcule ensuite les indicateurs des biens).
- DVF : relancer après chaque publication semestrielle (ajouter l'année dans `years`).
- BD TOPO : trimestrielle ; l'upsert est idempotent (clé `cleabs`). RGE ALTI : l'échantillon est recréé à chaque run.

## Alternatives si une source se montre instable
- Overpass indisponible : changer `overpass_url` (autre instance) ou importer un extrait Geofabrik dans `poi`.
- Transports : référentiel d'arrêts IDFM (data.iledefrance-mobilites.fr) → écrire des `poi` de `kind` `station`/`stop`.
- BD TOPO via WFS trop lent : télécharger le GPKG départemental IGN et l'importer avec `ogr2ogr` dans `building`.

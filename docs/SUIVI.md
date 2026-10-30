# Suivi

## Fait (2026-10-30)
- Socle : Docker Compose (db PostGIS, backend, worker, frontend nginx), Makefile, `.env.example`, config YAML, Alembic.
- Back : modèles, auth mot de passe+JWT, API biens/recherche/filtres/marché/connecteurs/export CSV/photos/prefill, alertes (SMTP ou fichier), worker.
- Calculs : dégagement 8 secteurs, vis-à-vis, qualité de vue, bruit, score pondéré + filtres durs + mode élargir (tests unitaires).
- Connecteurs implémentés : DVF, BAN, DPE ADEME, Géorisques, OSM, transports, Sitadel (URL à fournir), BD TOPO, RGE ALTI. 5 squelettes d'annonces désactivés.
- Front : filtres pondérés (URL partageable, filtres enregistrés, préréglage), liste+carte, fiche, 3D (extrusion + cône), formulaire avec pré-remplissage, marché, sources.
- Vérifié en réel : DVF (35 691 ventes, 134 communes), BAN+DPE+Géorisques+altimétrie (pré-remplissage), BD TOPO (2 617 bâtiments sur Évry).
- Qualité : pytest 10 OK, ruff OK, mypy strict OK, tsc/eslint/vitest OK, `docker compose up` OK.

## Refonte « site d'annonces » (2026-10-30)
- Front réécrit : filtres de base, cartes, fiche simple, carte 2D, ajout simplifié. Anciens panneaux de poids/marché/sources supprimés du front.
- Nouveau connecteur `interactives` (36h-immo.com, JSON-LD, robots.txt) ; `GET /api/listings`.
- Backend scoring/alertes/marché conservé mais non exposé (candidat à suppression si inutile).

## Sources + score + pédagogie (2026-10-30)
- Nouveaux connecteurs : `programmes` (34 offres 91/78), `viager` (24+39 « à la vente »), `interactives`/`encheres` étendus au 78. Total ≈ 143 annonces.
- Score « Mes préférences » (7 curseurs + 3 cibles) trié par défaut ; fiche « Pourquoi ce score ? » ; encadrés pédagogiques ; page « Comprendre les ventes » avec chiffres MdB Scanner.
- Disparition d'annonces gérée (`gone`), enchères passées masquées.
- Testé en réel : programmes, viager, API listings. Non testé visuellement (pas de navigateur dans l'environnement).

## À faire
- Vérifier le rendu à l'écran (cartes, préférences, guide) ; ajuster les textes pédagogiques avec un professionnel (notaire/avocat) avant tout usage public.
- Sources écartées (voir README) ; avoventes.fr et résultats passés de Licitor (prix réels d'adjudication) seraient des ajouts possibles.
- Plus de sources d'offres : vente-hlm.fr (bailleurs), encheres-publiques.com (signaux IA restrictifs, non fait), notaires (JS).
- Notaires : pas de scraping possible proprement (JS) ; piste = alertes e-mail (Gmail) ou flux officiel.
- Enchères : 16 biens réels du 91 importés (licitor) ; autres sites d'enchères non traités.
- Tester OSM / transports / RGE ALTI / Sitadel sur données réelles (non exécutés complets : volumes Overpass).
- Tests d'intégration API (base de test PostGIS) ; test front du composant FilterPanel.
- Mapillary/Street View : liens seulement (pas d'intégration d'images).
- Évolution des prix : annuelle seulement (pas trimestrielle).
- Connecteurs d'annonces : à implémenter un par un après vérification juridique.

## Décisions
- Overpass `out geom` + shapely `polygonize` pour les relations (forêts) : évite un dump OSM.
- Cellules de marché 1 km en Lambert-93 faute d'IRIS ouverts simples ; repli sur la commune si < 10 ventes.
- Score non stocké : permet de changer les poids sans recalcul.

## Questions ouvertes
- Fournir l'URL Sitadel du millésime voulu ? Souhaite-t-on IDFM plutôt qu'OSM pour les transports ?
- Exposition en ligne : HTTPS + protection des photos à prévoir.
- tokenwar : voir rapport d'examen dans la conversation (non installé, en attente d'accord).

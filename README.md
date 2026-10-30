# Ilo - recherche immobilière en Essonne (91)

Outil local d'aide à la recherche d'un appartement (ou maison) selon des critères **qualitatifs** : hauteur, vue, absence de
vis-à-vis, luminosité. Il s'appuie sur des **données ouvertes** (DVF, DPE ADEME, BAN, Géorisques, IGN BD TOPO / RGE ALTI,
OpenStreetMap, Sitadel) et sur la saisie manuelle de biens trouvés hors portails (notaires, enchères, bailleurs…).
Principe : **score pondéré et filtres souples**, jamais d'exclusion sauf filtre « indispensable » explicite.

## Premier lancement

```bash
cp .env.example .env        # changer APP_PASSWORD et SECRET_KEY (ou AUTH_ENABLED=false en local)
make up                     # = docker compose up --build -d
make seed                   # optionnel : 4 biens fictifs de démonstration
```
Interface : <http://localhost:8080> · API : <http://localhost:8000/docs>.

## Import initial des données

| Étape | Commande | Taille / durée indicative |
|---|---|---|
| Prix réels + stats marché | `make ingest SRC=dvf` | ~35 000 ventes (3 ans), 1-2 min |
| Parcs, forêts, eau, rail, axes | `make ingest SRC=osm` | Overpass, quelques minutes |
| Gares et arrêts | `make ingest SRC=transports` | Overpass |
| **Bâtiments (vue/vis-à-vis/3D)** | `make ingest SRC=ign_bdtopo` | **lourd** : tout le 91 = plusieurs centaines de milliers de bâtiments, plusieurs dizaines de minutes ; limiter avec `connectors.ign_bdtopo.bbox` dans `config/app.yaml` |
| Relief (secteurs en hauteur) | `make ingest SRC=ign_rgealti` | grille de 250 m via le service IGN (~50 000 points) ; limiter avec `bbox` |
| Permis de construire | renseigner `connectors.sitadel.url`, activer, `make ingest SRC=sitadel` | l'URL change à chaque millésime |

Sans BD TOPO, l'outil fonctionne mais **vis-à-vis et ciel visible ne sont pas calculés** (affiché dans la fiche, score neutre).
Les enrichissements DPE / Géorisques / BAN s'appliquent automatiquement aux biens saisis (`Pré-remplir`) et par le worker.
Le worker (`docker compose logs worker`) rejoue les ingestions activées selon leur `schedule` cron.

## Utilisation

- **Biens** : filtres à gauche (importance 0-5 par critère, plage idéale/acceptable, « indispensable » optionnel), liste triable,
  carte synchronisée. Le filtre complet est dans l'URL (`#f=…`) donc partageable. Préréglage « Vue dégagée en hauteur ».
- **Fiche** : score détaillé, dégagement par direction, vis-à-vis expliqué, comparaison aux ventes DVF voisines, DPE, risques,
  transports, **bouton « Voir en 3D »** (bâtiments extrudés + cône de vue), liens Street View / Mapillary / Google Earth.
- **Notes de visite** (vue, lumière, vis-à-vis, photos) : elles remplacent l'estimation et pèsent 1,5× plus.
- **+ Ajouter** : coller une adresse puis « Pré-remplir » (géocodage, DPE, risques, prix du secteur, indicateurs de vue).
- **Élargir la recherche** : montre aussi les biens « quasi éligibles » (marge de 15 % sur les filtres indispensables).
- **Alertes** : filtre enregistré avec un seuil « Alerte ≥ » → e-mail (si SMTP configuré) et/ou `data/alerts.log`.
- Export CSV des résultats filtrés et classés.

## Commandes

`make up|down|logs|migrate|ingest|seed|test|lint` (voir `Makefile`).

## Choix et limites (à lire)

- **Pas de scraping de portails.** Les connecteurs « biens à vendre » (`notaires`, `encheres`, `bailleurs`, `brs_psla`,
  `appels_projets`) sont des **squelettes désactivés** : vérifier les CGU, privilégier API officielle / partenariat.
- Sitadel ne fournit pas de coordonnées : seuls les projets ≥ 10 logements avec adresse sont géocodés (BAN).
- DVF : seules les mutations « Vente » à un seul local sont retenues (pas de ventes multi-lots ambiguës).
- Transports : OpenStreetMap par défaut ; le référentiel IDFM peut s'y substituer (voir `docs/connecteurs.md`).
- Le dataset ADEME (`dpe03existant`) et les URL Sitadel évoluent : les adresses sont dans `config/app.yaml`.
- Les indicateurs de vue sont des **estimations géométriques** (voir `docs/calculs.md`) : végétation, balcons et bâtiments non
  référencés ne sont pas vus. Les notes de visite font foi.
- Le calcul des scores se fait en mémoire sur tous les biens : prévu pour des milliers de biens, pas des millions.
- Les photos sont servies sans authentification (noms aléatoires) ; mettre l'outil derrière HTTPS avant exposition publique.
- Données OSM : © contributeurs OpenStreetMap (ODbL). Fond de carte : OpenFreeMap (configurable via `MAP_STYLE_URL`).

## Documentation

`docs/architecture.md` (schéma) · `docs/connecteurs.md` (ajouter une source, mettre à jour) · `docs/calculs.md` (dégagement,
vis-à-vis, vue, score) · `docs/SUIVI.md` (état d'avancement) · `CLAUDE.md` (mémo court pour l'assistant).

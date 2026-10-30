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

Un site d'annonces classique, pour des offres **absentes des grands portails** (enchères judiciaires, ventes interactives…) :
- Barre de filtres simple : lieu, type, prix max, surface, pièces, étage, balcon/terrasse, ascenseur, favoris, source.
- Liste de cartes (photo, prix, €/m², pièces, surface, étage) ou carte ; tri par date, prix, prix au m², surface.
- Fiche : photos, caractéristiques, lien vers l'annonce d'origine, favori / masquer. Section repliable « Quartier et vue » (estimations).
- **+ Ajouter une annonce** : lien, adresse (placée sur la carte automatiquement) et caractéristiques.
- Les filtres sont dans l'URL (`#…`) donc partageables.
- L'API garde aussi le moteur de score avancé (`/api/properties/search`, vis-à-vis, 3D) non exposé dans l'interface.

## Commandes

`make up|down|logs|migrate|ingest|seed|test|lint` (voir `Makefile`).

## Choix et limites (à lire)

- **Biens à vendre.** Deux sources actives (`encheres`, `interactives` = 36h-immo.com, ~10 biens du 91) : enchères judiciaires immobilières du 91 (licitor.com) et ventes interactives ; collecte quotidienne via
  `app/scraping.py` (robots.txt obligatoire, 1 requête / 3 s, User-Agent explicite, aucun contournement). Le prix affiché est la
  **mise à prix**, pas un prix de vente (écart au marché non calculé). **Vérifiez les CGU du site** avant tout usage durable : c'est votre responsabilité.
- `notaires` : **non implémenté** - le site immobilier.notaires.fr affiche ses annonces via JavaScript/API interne ; l'exploiter
  demanderait un navigateur headless ou une API non documentée (hors cadre). Voir une API/flux officiel ou les alertes e-mail.
- `bailleurs`, `brs_psla`, `appels_projets` : squelettes désactivés (pas de source ouverte exploitable identifiée).
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

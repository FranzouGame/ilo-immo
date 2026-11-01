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

Un site d'annonces pour des offres **peu visibles sur les grands portails**, avec un score personnalisé et des explications :

- **Annonces** : filtres de base (lieu, département, type, prix max, surface, pièces, étage, balcon/terrasse, ascenseur, favoris, source), liste ou carte.
- **Score (0-100)** : « ⭐ Mes préférences » règle l'importance (0 à 5) de 7 critères (prix, surface, étage, vue/lumière, gare, balcon, bonne affaire) et vos valeurs cibles
  (budget idéal, surface, étage). Les annonces sont classées par défaut du meilleur au moins bon score ; une donnée manquante est neutre (jamais éliminatoire).
  Pour une enchère, c'est le **prix final estimé** qui est noté, pas la mise à prix.
- **Fiche** : photos, caractéristiques, « Pourquoi ce score ? », encadré pédagogique propre à la catégorie (enchère : consignation, avocat, surenchère,
  prix final probable ; viager : bouquet, rente, décote ; vente interactive ; BRS/PSLA/TVA 5,5 %/vente HLM), lien vers l'annonce d'origine.
- **Comprendre les ventes** : guide complet par type de vente, avec les chiffres réels des enchères (Essonne 51 %, Yvelines 55 % du prix voisin, étude MdB Scanner / data.gouv.fr).
- **+ Ajouter une annonce** : lien, adresse (placée sur la carte automatiquement), caractéristiques.
- Les filtres et préférences sont dans l'URL (`#…`), donc partageables.

## Publier sur GitHub Pages (site public)

GitHub Pages ne sert que des pages statiques. Le workflow `.github/workflows/pages.yml` fait donc tout le travail dans GitHub Actions, chaque jour et à chaque `push` :
base PostGIS jetable -> collecte des annonces (mêmes connecteurs) -> export `listings.json` -> build du front en mode statique -> déploiement.
Filtres, score « Mes préférences » et tri sont calculés dans le navigateur ; favoris et masquages restent dans le navigateur du visiteur (localStorage).

1. Pousser le dépôt sur GitHub (branche `main`).
2. *Settings -> Pages -> Source : GitHub Actions* (ou `gh api -X POST repos/<user>/<repo>/pages -f build_type=workflow`).
3. Lancer le workflow (*Actions -> Site (GitHub Pages) -> Run workflow*). Adresse : `https://<user>.github.io/<repo>/`.

Dans le site public : pas de mot de passe, pas de saisie d'annonce, **pas de photos** (`static_export.include_photos: false` dans `config/app.yaml`),
pas de notes ni d'âge/sexe des vendeurs de viager, balise `noindex`. Garde-fou : un export trop petit (source bloquée depuis GitHub) annule le déploiement.
Un dépôt public sans activité pendant 60 jours voit ses tâches planifiées suspendues par GitHub : relancer le workflow à la main.

## Mot de passe PostgreSQL

Le mot de passe de la base (`POSTGRES_PASSWORD`) n'est lu par PostgreSQL qu'à la **première** création du volume. Si vous le changez ensuite :
`docker compose exec -T db sh -c 'printf "%s\n" "ALTER USER :\"u\" PASSWORD :'"'"'pw'"'"';" | psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v pw="$POSTGRES_PASSWORD" -v u="$POSTGRES_USER"'`,
ou `docker compose down -v` (efface les données ; les annonces se recollent avec `make ingest`). Les caractères spéciaux (`@`, `:`, `/`) sont acceptés.

## Commandes

`make up|down|logs|migrate|ingest|seed|test|lint` (voir `Makefile`).

## Choix et limites (à lire)

- **Sources d'annonces actives** (collecte quotidienne via `app/scraping.py` : robots.txt obligatoire, 1 requête / 3 s, User-Agent explicite, aucun contournement) :
  `encheres` (Licitor, enchères judiciaires), `interactives` (36h-immo.com), `programmes` (proprietairemaintenant.fr : TVA 5,5 %, BRS, PSLA, prix maîtrisé, vente HLM),
  `viager` (Renée Costes). **Vérifiez les CGU de chaque site** avant usage durable : c'est votre responsabilité. Les photos sont affichées par lien direct vers la source.
- Une annonce qui disparaît de sa source est masquée (`gone`) ; une enchère dont la date est passée aussi.
- Prix : mise à prix (enchère), prix de départ (interactive), « à partir de » (programmes), valeur occupée (viager) - jamais présentés comme un prix de vente classique.
- **Non collectés** : annonces des notaires (immobilier.notaires.fr : affichage par JavaScript / API interne), encheres-publiques.com (accès bloqué aux robots), Agorastore et
  Avoventes (JavaScript), Interenchères (recherche interdite par robots.txt), portails commerciaux. Piste pour les notaires : alertes e-mail du site.
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

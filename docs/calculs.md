# Calculs (et leurs limites)

Tous les seuils sont dans `config/app.yaml` (`view:` et `scoring:`).

## Altitude de la fenêtre
`altitude sol + étage × 2,7 m` (+1,5 m si l'étage est inconnu). Altitude du sol : bâtiment propre (BD TOPO) → point de relief le plus
proche → service altimétrie IGN. Le bâtiment propre est le plus proche à ≤ 15 m du point géocodé ; il est exclu des obstacles.
Étage relatif = étage / nombre d'étages (saisi, sinon BD TOPO).

## Dégagement par secteur
8 secteurs de 45°, 7 rayons par secteur, portée 300 m. Pour chaque rayon : premier bâtiment dont le **toit dépasse la fenêtre**.
Sorties par secteur : distance minimale, part de rayons bloqués, écart de hauteur, étages au-dessus. « Ciel visible » = 100 × (1 − angle
moyen d'obstruction / 90°). *Limites* : toit = altitude max BD TOPO (pas de pente, pas de végétation) ; point géocodé à la rue, pas à la façade.

## Risque de vis-à-vis (0-100)
Par secteur : `100 × (1 − distance / 50 m) × (0,5 + 0,5 × min(1, écart/(3 étages)))`. Orientation de façade connue → pire valeur des 3 secteurs
du cône (façade ±45°) ; inconnue → **meilleur secteur**. L'explication est générée en clair (« Immeuble à 18 m (NE), 3 étages plus haut »).

## Qualité de vue (0-100)
Base 50. Bonus : parc/forêt/eau (≤ 800 m, décroissant avec la distance, ×0,5 hors du cône), secteur ouvert à 300 m (+10), bâtiment situé ≥ 5/15 m
au-dessus du terrain alentour (+5/+10) ; plafond +35. Malus : grand axe (≤ 150 m), voie ferrée (≤ 250 m), zone industrielle (≤ 300 m) ; plafond −35.
Bruit : indice séparé fondé sur axes et rail uniquement (aucune mesure acoustique réelle).

## Score (0-100)
Pour chaque critère de poids > 0 : note 0-1 (1 dans la plage idéale, décroissance linéaire jusqu'à 0 au bord de la plage acceptable ; booléen ; préférences).
Donnée inconnue → 0,5 (neutre, pas d'exclusion). Note de visite → `note/10` avec poids × 1,5. Score = moyenne pondérée × 100.
Filtres « indispensables » : seule exclusion ; valeur inconnue = non exclu ; mode « élargir » = marge de 15 % signalée « quasi éligible ».

## Écart au marché
`prix/m² du bien` vs médiane DVF du carré de 1 km (≥ 10 ventes) sinon de la commune, même type de bien, toutes années.

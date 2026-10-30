export interface Block { h: string; p?: string; list?: string[] }
export interface GuideEntry { id: string; icon: string; title: string; tagline: string; blocks: Block[] }

export const GUIDE: GuideEntry[] = [
  { id: 'enchere', icon: '⚖️', title: 'Vente aux enchères judiciaire', tagline: 'Un bien saisi, vendu publiquement au tribunal, souvent bien en dessous du prix du marché.',
    blocks: [
      { h: "C'est quoi ?", p: "Un créancier (le plus souvent une banque) fait vendre le logement d'un propriétaire qui n'a pas remboursé ses dettes. La vente a lieu à l'audience du juge de l'exécution (tribunal judiciaire). Le propriétaire n'a pas choisi de vendre : on parle de saisie immobilière." },
      { h: 'Pourquoi c\'est moins cher ?', list: [
        "La mise à prix (prix de départ) est fixée volontairement très bas pour attirer les enchérisseurs : en médiane 27 % du prix des ventes voisines.",
        "Le bien est parfois occupé, à rénover, sans visite approfondie possible, et la vente se fait sans garantie des vices cachés.",
        "Il faut avoir son financement prêt à l'avance (pas de condition suspensive de prêt) : cela écarte beaucoup d'acheteurs.",
        "Résultat observé (étude MdB Scanner sur 2 961 logements) : un logement sur deux part à moins de 60 % du prix des ventes voisines, hors frais." ] },
      { h: 'Comment ça se passe, étape par étape', list: [
        "1. Lire l'annonce et le cahier des conditions de vente (consultable auprès de l'avocat qui poursuit la vente, ou au greffe) : état, occupation, diagnostics, charges.",
        "2. Visiter : un commissaire de justice organise une visite à date fixe (indiquée dans l'annonce). C'est souvent la seule.",
        "3. Prendre un avocat inscrit au barreau du tribunal concerné : il est obligatoire pour enchérir. Vous ne parlez pas vous-même à l'audience.",
        "4. Consigner : chèque de banque remis à l'avocat, d'au moins 10 % de la mise à prix (3 000 € minimum). Il est rendu si vous n'êtes pas adjudicataire.",
        "5. Audience : l'avocat enchérit pour vous jusqu'à votre plafond. Le plus offrant devient adjudicataire.",
        "6. Surenchère : pendant 10 jours, toute personne peut surenchérir d'au moins 10 % du prix (par avocat) ; une nouvelle audience a alors lieu.",
        "7. Payer : le prix et les frais dans un délai court fixé par le cahier des conditions de vente (en général de l'ordre de deux mois après que la vente est définitive), sinon le bien est remis en vente à vos frais (« folle enchère »). Le jugement d'adjudication fait office de titre de propriété." ] },
      { h: 'Les pièges à connaître', list: [
        "Des frais s'ajoutent au prix (droits de mutation, émoluments d'avocat, frais de poursuite) : le détail est dans le cahier des conditions de vente.",
        "Un bien « occupé » (locataire ou ancien propriétaire) peut être difficile à récupérer : il part moins cher (appartements occupés ≈ 63 % du prix voisin contre 71 % pour les libres, mêmes conditions).",
        "Travaux, charges de copropriété impayées, absence de garantie : budgétez une marge.",
        "Les belles affaires attirent les enchérisseurs : 9 % des logements partent à 100 % du prix voisin ou plus." ] },
      { h: 'Qui peut acheter ?', p: "Tout le monde, particulier ou investisseur, à condition de passer par un avocat et de déposer la consignation." },
    ] },
  { id: 'interactive', icon: '🖥️', title: 'Vente interactive (notaire / agence)', tagline: 'Une vente classique, mais le prix se forme par des offres successives en ligne.',
    blocks: [
      { h: "C'est quoi ?", p: "Le vendeur a choisi de vendre (ce n'est pas une saisie). Le bien est présenté sur une plateforme avec un prix de départ ; pendant une période d'offres (typiquement un jour et demi), chaque acquéreur voit les offres des autres et peut surenchérir. Le vendeur retient ensuite une offre." },
      { h: 'Pourquoi c\'est intéressant ?', list: [
        "Prix de départ souvent attractif pour attirer du monde : il peut monter nettement.",
        "Transparence : tous les acquéreurs voient les offres en temps réel.",
        "Pas de tribunal ni d'avocat obligatoire : c'est une vente normale devant notaire." ] },
      { h: 'Comment ça se passe ?', list: [
        "1. Visites organisées avant l'ouverture des offres.",
        "2. Inscription sur la plateforme, avec pièces d'identité et justificatif de financement si demandé.",
        "3. Période d'offres en ligne : chacun propose un prix.",
        "4. Le vendeur accepte une offre : compromis ou promesse de vente.",
        "5. Délai de rétractation de 10 jours après réception du compromis (loi SRU) pour un acquéreur particulier, puis acte chez le notaire." ] },
      { h: 'À savoir', list: [
        "Le prix de départ n'est PAS le prix final.",
        "Les frais de notaire habituels s'appliquent comme pour toute vente de bien ancien.",
        "Vérifiez dans le compromis les conditions suspensives (prêt notamment)." ] },
    ] },
  { id: 'viager', icon: '⏳', title: 'Viager', tagline: 'Vous achetez en payant un capital puis une rente à vie au vendeur.',
    blocks: [
      { h: "C'est quoi ?", p: "L'acheteur (débirentier) paie un bouquet au départ, puis une rente mensuelle au vendeur (crédirentier) jusqu'à son décès. Le prix total dépend donc de la durée de vie du vendeur : c'est un contrat avec aléa." },
      { h: 'Les trois formules', list: [
        "Viager occupé : le vendeur continue de vivre dans le logement (droit d'usage et d'habitation). Vous en prenez possession à son décès. Le prix est décoté par rapport à la valeur libre ; plus le vendeur est âgé, plus la décote est forte.",
        "Viager libre : vous disposez du bien tout de suite (pour y habiter ou le louer). Rente plus élevée, pas de décote d'occupation.",
        "Vente en nue-propriété : vous achetez la nue-propriété, le vendeur garde l'usufruit ; vous retrouvez la pleine propriété au décès ou à un terme fixé." ] },
      { h: 'Lire une annonce de viager', list: [
        "Bouquet : somme versée à la signature.",
        "Rente : montant mensuel, en général indexé sur l'inflation.",
        "Valeur libre : prix du bien s'il était vendu libre. Valeur occupée (« prix d'achat » dans nos fiches) : bouquet + valeur capitalisée de la rente.",
        "Décote : écart entre valeur libre et valeur occupée." ] },
      { h: 'Les points de vigilance', list: [
        "Vous payez tant que le vendeur vit : vous pouvez dépasser la valeur du bien.",
        "Une rente se finance sur vos revenus : pas d'achat « à crédit » classique.",
        "Répartition des charges : en général, les grosses réparations et souvent la taxe foncière incombent à l'acheteur, les charges courantes à l'occupant ; vérifiez le contrat.",
        "Faites-vous conseiller par un notaire avant de signer." ] },
    ] },
  { id: 'aide', icon: '🏗️', title: 'Accession aidée : BRS, PSLA, TVA 5,5 %, prix maîtrisé, vente HLM', tagline: 'Des logements neufs ou de bailleurs vendus moins chers, sous conditions de ressources.',
    blocks: [
      { h: 'BRS - Bail Réel Solidaire', list: [
        "Vous achetez les murs ; le terrain reste à un organisme de foncier solidaire (OFS) qui vous le loue : vous payez une petite redevance mensuelle.",
        "Prix en général nettement inférieur au marché (le terrain n'est pas compris), TVA réduite à 5,5 %.",
        "Conditions : résidence principale, revenus sous plafonds.",
        "Revente encadrée : vous revendez à un acquéreur lui aussi sous plafonds, à un prix encadré ; le bail est « rechargé » pour l'acheteur suivant." ] },
      { h: 'PSLA - Prêt Social Location-Accession', list: [
        "Vous commencez par louer le logement neuf (redevance = loyer + part qui prépare l'achat), puis vous levez l'option d'achat au prix fixé dès le départ.",
        "TVA à 5,5 %, plafonds de ressources et de prix.",
        "Des garanties de rachat et de relogement existent si votre situation change pendant la phase locative." ] },
      { h: 'TVA 5,5 % et prix maîtrisé', list: [
        "TVA réduite pour l'achat d'un logement neuf en quartier prioritaire de la politique de la ville (ou à moins de 300 m), en résidence principale et sous plafonds de ressources.",
        "Accession à prix maîtrisé : programmes dont les prix sont plafonnés avec la collectivité, pour viser des ménages modestes ou intermédiaires." ] },
      { h: 'Vente HLM', list: [
        "Un bailleur social vend des logements de son parc (anciens), en priorité aux locataires en place puis à d'autres acquéreurs sous conditions.",
        "Prix fixé par le bailleur après avis du service des Domaines, souvent inférieur au marché.",
        "Le bailleur reste souvent copropriétaire de l'immeuble ; des conditions de revente peuvent s'appliquer pendant quelques années." ] },
      { h: 'Dans tous les cas', list: ["Vérifiez votre éligibilité (plafonds de ressources) avant de visiter.", "Les prix « à partir de » concernent le lot le moins cher du programme."] },
    ] },
]

export interface AuctionStat { place: string; paid: number; q1: number; q3: number; reserve: number }
export const AUCTION_STATS: AuctionStat[] = [
  { place: 'Essonne (91)', paid: 51, q1: 38, q3: 67, reserve: 24 },
  { place: 'Yvelines (78)', paid: 55, q1: 43, q3: 67, reserve: 33 },
  { place: 'France (étude)', paid: 60, q1: 44, q3: 78, reserve: 27 },
]
export const AUCTION_SOURCE = {
  label: "Observatoire MdB Scanner - « Prix d'adjudication des logements vendus aux enchères judiciaires, comparés aux ventes voisines (2022-2026) »",
  url: 'https://www.data.gouv.fr/datasets/prix-dadjudication-des-logements-vendus-aux-encheres-judiciaires-compares-aux-ventes-voisines-2022-2026-1',
}
export const RESERVE_TABLE = [
  { tranche: 'moins de 30 000 €', multiple: '× 3,3' },
  { tranche: '30 000 à 80 000 €', multiple: '× 2,1' },
  { tranche: '80 000 à 150 000 €', multiple: '× 1,7' },
  { tranche: '150 000 à 300 000 €', multiple: '× 1,3' },
  { tranche: '300 000 € et plus', multiple: '× 1,1' },
]

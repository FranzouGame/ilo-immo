import { eur } from '../lib/filters'
import { kindOf, whenLabel } from '../lib/kinds'
import type { Property } from '../types'

/** Encadré pédagogique sur la fiche : explique la catégorie et les chiffres propres à cette annonce. */
export default function InfoBox({ p, openGuide }: { p: Property; openGuide: (id: string) => void }) {
  const k = kindOf(p)
  const a = p.computed.auction
  const v = p.custom['viager'] as { bouquet?: number; rente?: number; valeur_libre?: number; decote_pct?: number; ages?: string[]; type?: string } | undefined
  const when = whenLabel(p)
  const tribunal = p.custom['tribunal'] as string | undefined
  return (
    <section className="infobox">
      <h3>{k.icon} {k.label} - comment ça marche ?</h3>
      <p>{k.blurb}</p>
      {p.kind === 'enchere' && a && (
        <ul>
          <li><b>Mise à prix : {eur(a.reserve)}</b> - ce n'est pas le prix de vente. En médiane, le prix final est {a.multiple.toString().replace('.', ',')} fois la mise à prix pour cette tranche.</li>
          <li>Pour enchérir : un <b>avocat</b> du barreau du tribunal{tribunal ? ` (${tribunal})` : ''} et une <b>consignation d'environ {eur(a.deposit)}</b> (10 % de la mise à prix, 3 000 € minimum), rendue si vous ne gagnez pas.</li>
          {a.by_market
            ? <li>Prix final probable : <b>≈ {eur(a.by_market.median)}</b> (fourchette {eur(a.by_market.q1)} - {eur(a.by_market.q3)}). Valeur du secteur ≈ {eur(a.market_value)} : la mise à prix en représente {a.reserve_pct_of_value} %, et pour cette tranche de prix un logement part en médiane à {a.paid_pct.median} % du prix des ventes voisines{a.occupied ? ' (bien occupé : décote supplémentaire incluse)' : ''}.</li>
            : <li>Estimation par la mise à prix : <b>≈ {eur(a.by_multiple)}</b> (surface ou prix du secteur inconnus).</li>}
          {p.custom['occupation'] === 'libre' && <li>✓ L'annonce indique un bien <b>libre</b> d'occupation ({String(p.custom['occupation_note'] ?? 'à confirmer sur le cahier des conditions de vente')}).</li>}
          {p.custom['occupation'] === 'occupé' && <li>⚠ Bien <b>occupé</b> : plus difficile à récupérer, décote plus forte mais risque de procédure d'expulsion. À confirmer sur le cahier des conditions de vente.</li>}
          {typeof p.custom['visite'] === 'string' && <li>🔎 Visite : <b>{String(p.custom['visite'])}</b> (commissaire de justice).</li>}
          <li>Dans les 10 jours après la vente, une surenchère de {a.surenchere_pct} % est possible : l'adjudication n'est définitive qu'ensuite.</li>
          {when && <li><b>{when}</b> - {String(p.custom['vente_le'] ?? '').slice(0, 10)}. Visite organisée par un commissaire de justice (voir l'annonce d'origine).</li>}
        </ul>
      )}
      {p.kind === 'viager' && v && (
        <ul>
          <li>Vous versez <b>{eur(v.bouquet)}</b> à la signature puis <b>{v.rente ?? '?'} €/mois</b> au vendeur{v.ages && v.ages.length ? ` (${v.ages.join(', ')})` : ''} jusqu'à son décès.</li>
          <li>{v.type ?? 'Viager'} : {String(v.type ?? '').toLowerCase().includes('occup') ? 'le vendeur reste dans le logement, vous y entrez à son décès.' : 'vous disposez du bien tout de suite.'}</li>
          {v.valeur_libre && <li>Valeur du bien libre : {eur(v.valeur_libre)}{v.decote_pct ? ` ; décote de ${v.decote_pct} % grâce à l'occupation` : ''}. Le prix affiché (≈ {eur(p.price)}) est la valeur occupée.</li>}
          <li>Plus le vendeur vit longtemps, plus le coût total augmente : c'est un pari sur la durée.</li>
        </ul>
      )}
      {p.kind === 'notaire' && (
        <ul>
          <li>Annonce publiée par une étude notariale : <b>vente classique</b>, négociable, avec les frais de notaire habituels (≈ 7-8 % dans l'ancien).</li>
          <li>Demandez à l'étude le dossier de diagnostics, les charges de copropriété et la taxe foncière avant toute offre.</li>
        </ul>
      )}
      {p.kind === 'interactive' && (
        <ul>
          <li>Le prix affiché ({eur(p.price)}) est un <b>prix de départ</b> : les offres successives le font monter pendant la période d'offres.</li>
          <li>Après acceptation de l'offre : compromis, <b>10 jours de rétractation</b>, puis acte chez le notaire.</li>
        </ul>
      )}
      {p.kind === 'aide' && (
        <ul>
          <li>Dispositif : <b>{String(p.custom['dispositif_label'] ?? 'accession aidée')}</b>{p.custom['livraison'] ? ` - livraison : ${String(p.custom['livraison'])}` : ''}.</li>
          <li>« À partir de » = prix du lot le moins cher du programme. Des plafonds de ressources s'appliquent en général.</li>
        </ul>
      )}
      {k.guide !== 'general' && <button className="link" onClick={() => openGuide(k.guide)}>Lire le guide complet →</button>}
    </section>
  )
}

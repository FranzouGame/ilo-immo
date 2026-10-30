import type { Property } from '../types'
import { eur } from './filters'

export interface KindInfo { label: string; icon: string; blurb: string; guide: string }

export const KINDS: Record<string, KindInfo> = {
  enchere: { label: 'Enchère judiciaire', icon: '⚖️', guide: 'enchere',
    blurb: 'Vente forcée au tribunal : le prix de départ (mise à prix) est volontairement bas, le prix final se décide aux enchères.' },
  interactive: { label: 'Vente interactive', icon: '🖥️', guide: 'interactive',
    blurb: 'Vente classique mais mise en concurrence en ligne : on part d\'un prix de départ et les offres montent pendant quelques heures.' },
  viager: { label: 'Viager', icon: '⏳', guide: 'viager',
    blurb: 'On paie un capital (bouquet) puis une rente au vendeur jusqu\'à son décès ; le bien est souvent occupé par le vendeur.' },
  aide: { label: 'Accession aidée', icon: '🏗️', guide: 'aide',
    blurb: 'Logement neuf ou de bailleur social vendu à prix réduit (TVA 5,5 %, BRS, PSLA, prix maîtrisé…) sous conditions.' },
  autre: { label: 'Annonce', icon: '🏠', guide: 'general', blurb: 'Annonce saisie manuellement.' },
}

export const kindOf = (p: Property): KindInfo => KINDS[p.kind] ?? KINDS['autre']!

const dispositif = (p: Property): string => String(p.custom['dispositif_label'] ?? '')

/** Libellé court de la catégorie, ex. « Accession aidée · BRS ». */
export function kindLabel(p: Property): string {
  const k = kindOf(p)
  return p.kind === 'aide' && dispositif(p) ? `${k.label} · ${dispositif(p)}` : k.label
}

export function daysUntil(iso: unknown): number | null {
  if (typeof iso !== 'string') return null
  const d = (new Date(iso).getTime() - Date.now()) / 86400_000
  return Number.isFinite(d) ? Math.ceil(d) : null
}

/** Ligne de prix adaptée à la catégorie : la « mise à prix » d'une enchère n'est PAS un prix de vente. */
export function priceLines(p: Property): { main: string; sub: string | null } {
  const v = p.custom['viager'] as { bouquet?: number; rente?: number; valeur_libre?: number; decote_pct?: number } | undefined
  if (p.kind === 'enchere') {
    const est = p.computed.auction?.estimate
    return { main: `Mise à prix ${eur(p.price)}`, sub: est ? `Prix final probable ≈ ${eur(est)}` : null }
  }
  if (p.kind === 'viager' && v) {
    return { main: `Bouquet ${eur(v.bouquet)} + ${v.rente ?? '?'} €/mois`,
      sub: v.valeur_libre ? `Valeur libre ${eur(v.valeur_libre)}${v.decote_pct ? ` · décote ${v.decote_pct} %` : ''}` : null }
  }
  if (p.kind === 'interactive') return { main: `Départ ${eur(p.price)}`, sub: 'les offres montent en ligne' }
  if (p.kind === 'aide') return { main: `À partir de ${eur(p.price)}`, sub: null }
  return { main: eur(p.price), sub: p.price_m2 ? `${p.price_m2.toLocaleString('fr-FR')} €/m²` : null }
}

export function whenLabel(p: Property): string | null {
  const d = daysUntil(p.custom['vente_le'])
  if (d == null) return null
  return d <= 0 ? "Vente aujourd'hui" : d === 1 ? 'Vente demain' : `Vente dans ${d} jours`
}

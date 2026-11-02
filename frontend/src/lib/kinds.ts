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
  notaire: { label: 'Annonce de notaire', icon: '🏛️', guide: 'notaire',
    blurb: 'Bien présenté par une étude notariale : vente classique (frais de notaire habituels), souvent peu relayée sur les grands portails.' },
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

/** Variation du prix récente (30 jours) : -5 = baisse de 5 %. */
export function priceChange(p: Property): { pct: number; from: number } | null {
  const last = p.price_history?.at(-1)
  if (!last || !p.price || Date.now() - new Date(last.date).getTime() > 30 * 86400_000) return null
  const pct = Math.round((100 * (p.price - last.price)) / last.price)
  return pct === 0 ? null : { pct, from: last.price }
}

/** Points de vigilance visibles sur la carte. */
export function flags(p: Property): { text: string; tone: 'ok' | 'warn' }[] {
  const out: { text: string; tone: 'ok' | 'warn' }[] = []
  const occ = p.custom['occupation']
  if (p.kind === 'enchere' && occ === 'libre') out.push({ text: 'Libre', tone: 'ok' })
  if (p.kind === 'enchere' && occ === 'occupé') out.push({ text: 'Occupé', tone: 'warn' })
  if (p.kind === 'enchere' && occ === 'inconnue') out.push({ text: 'Occupation à vérifier', tone: 'warn' })
  if (p.kind === 'viager' && String((p.custom['viager'] as { type?: string } | undefined)?.type ?? '').toLowerCase().includes('occup')) out.push({ text: 'Vendeur sur place', tone: 'warn' })
  return out
}

/** « Pépite » : bon score + décote apparente forte ; jamais pour viager/accession aidée ; enchère seulement si libre. Règle simple, expliquée dans le guide. */
export function isGem(p: Property): boolean {
  const deal = p.computed.deal_pct ?? 0
  if (p.kind === 'aide' || p.kind === 'viager') return false // décotes structurelles (règles du dispositif / occupation), pas des affaires
  if (p.kind === 'enchere' && p.custom['occupation'] !== 'libre') return false // une enchère n'est une pépite que si elle est libre
  return p.score >= 70 && deal >= 30
}

export const isNew = (p: Property, lastVisit: number | null): boolean =>
  lastVisit != null ? new Date(p.created_at).getTime() > lastVisit : Date.now() - new Date(p.created_at).getTime() < 3 * 86400_000

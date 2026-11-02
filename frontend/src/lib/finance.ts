import type { Property } from '../types'

export interface Finance { rate_pct: number; years: number; down_payment: number }
export type Fees = Record<string, number>

const KEY = 'ilo_finance'
export function loadFinance(defaults: Finance): Finance {
  try {
    return { ...defaults, ...(JSON.parse(localStorage.getItem(KEY) ?? '{}') as Partial<Finance>) }
  } catch {
    return defaults
  }
}
export function saveFinance(f: Finance): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(f))
  } catch {
    /* stockage indisponible */
  }
}

/** Mensualité d'un prêt à taux fixe (hors assurance). */
export function monthly(principal: number, ratePct: number, years: number): number {
  const n = years * 12
  const r = ratePct / 100 / 12
  if (principal <= 0 || n <= 0) return 0
  return r === 0 ? principal / n : (principal * r) / (1 - (1 + r) ** -n)
}

export interface Cost { base: number; fees: number; total: number; loan: number; monthly: number }

/** Coût d'acquisition indicatif : prix retenu (estimation pour une enchère) + frais, moins l'apport. Pas pour le viager. */
export function cost(p: Property, fin: Finance, fees: Fees): Cost | null {
  if (p.kind === 'viager' || !p.price) return null
  const base = p.kind === 'enchere' ? (p.computed.auction?.estimate ?? p.price) : p.price
  const key = p.kind === 'enchere' ? 'enchere' : p.kind === 'aide' && p.custom['dispositif'] !== 'vente-hlm' ? 'neuf' : 'ancien'
  const f = Math.round((base * (fees[key] ?? 0)) / 100)
  const total = base + f
  const loan = Math.max(0, total - fin.down_payment)
  return { base, fees: f, total, loan, monthly: Math.round(monthly(loan, fin.rate_pct, fin.years)) }
}

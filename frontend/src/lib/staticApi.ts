/** Mode « site statique » (GitHub Pages) : les filtres et le score sont calculés dans le navigateur.
 *  Doit rester cohérent avec backend/app/simple_score.py et backend/app/scoring.py. */
import type { Filters, Property, ScoreDefaults } from '../types'
import type { Fees, Finance } from './finance'

export const STATIC = import.meta.env.VITE_STATIC === '1'

export interface Crit {
  key: string
  label: string
  kind: 'range' | 'bool' | 'set'
  field: string
  ideal?: [number | null, number | null]
  acceptable?: [number | null, number | null]
  weight: number
}
export interface StaticData {
  generated_at: string
  config: { departments: { code: string; name: string }[]; department_name: string; map: { center: [number, number]; zoom: number }; criteria: Crit[]; finance: Finance; fees_pct: Fees }
  defaults: ScoreDefaults
  items: Property[]
}

let cache: Promise<StaticData> | null = null
export const loadData = (): Promise<StaticData> => {
  cache ??= fetch(`${import.meta.env.BASE_URL}data/listings.json`).then((r) => {
    if (!r.ok) throw new Error(`Données indisponibles (${r.status})`)
    return r.json() as Promise<StaticData>
  })
  return cache
}

const GROUPS: Record<string, string[]> = {
  price: ['price'], surface: ['surface'], floor: ['floor', 'relative_floor'], view: ['view_quality', 'vis_a_vis', 'sky_view'],
  station: ['station_distance'], outdoor: ['balcony'], deal: ['market_gap'],
}

export function fit(v: number, ideal: [number | null, number | null], acc: [number | null, number | null]): number {
  const [lo, hi] = ideal
  const [alo, ahi] = acc
  if (lo != null && v < lo) return alo == null || v <= alo ? 0 : (v - alo) / (lo - alo)
  if (hi != null && v > hi) return ahi == null || v >= ahi ? 0 : (ahi - v) / (ahi - hi)
  return 1
}

const getField = (o: unknown, path: string): unknown =>
  path.split('.').reduce<unknown>((cur, k) => (cur != null && typeof cur === 'object' ? (cur as Record<string, unknown>)[k] : undefined), o)

const num = (s: string): number | null => (s !== '' && Number.isFinite(Number(s)) ? Number(s) : null)

/** Critères effectifs : poids des 7 groupes + cibles chiffrées (équivalent de simple_score.build_spec). */
export function buildCriteria(criteria: Crit[], f: Filters, d: ScoreDefaults): Crit[] {
  const w: Record<string, number> = {}
  for (const g of Object.keys(GROUPS)) {
    const v = num(f[`w_${g}` as keyof Filters] as string)
    w[g] = v ?? d.weights[g] ?? 0
  }
  const budget = num(f.budget) ?? d.budget
  const surface = num(f.surface_target) ?? d.surface
  const floor = num(f.floor_target) ?? d.floor
  return criteria.map((c) => {
    const g = Object.keys(GROUPS).find((k) => GROUPS[k]?.includes(c.key))
    const out: Crit = { ...c, weight: g ? (w[g] ?? 0) : 0 }
    if (c.key === 'price') { out.ideal = [null, budget]; out.acceptable = [null, Math.round(budget * 1.25)] }
    if (c.key === 'surface') { out.ideal = [surface, null]; out.acceptable = [Math.round(surface * 0.8), null] }
    if (c.key === 'floor') { out.ideal = [floor, null]; out.acceptable = [Math.max(0, floor - 2), null] }
    return out
  })
}

export function evaluate(p: Property, crit: Crit[]): { score: number; breakdown: Property['breakdown'] } {
  let total = 0
  let wsum = 0
  const breakdown: Property['breakdown'] = []
  for (const c of crit) {
    if (c.weight <= 0) continue
    const raw = getField(p, c.field)
    let s: number | null = null
    if (raw != null) s = c.kind === 'bool' ? (raw ? 1 : 0) : fit(Number(raw), c.ideal ?? [null, null], c.acceptable ?? [null, null])
    total += c.weight * (s ?? 0.5)
    wsum += c.weight
    breakdown.push({ key: c.key, label: c.label, weight: c.weight, value: raw, score: s == null ? null : Math.round(s * 100) / 100, manual: false })
  }
  return { score: wsum ? Math.round((100 * total) / wsum) : 0, breakdown }
}

const KEYS = { fav: 'ilo_fav', hidden: 'ilo_hidden' } as const
export type LocalSet = keyof typeof KEYS
export function readSet(k: LocalSet): Set<number> {
  try {
    return new Set(JSON.parse(localStorage.getItem(KEYS[k]) ?? '[]') as number[])
  } catch {
    return new Set()
  }
}
export function setStatusLocal(id: number, status: string): void {
  const fav = readSet('fav')
  const hidden = readSet('hidden')
  fav.delete(id)
  hidden.delete(id)
  if (status === 'favori') fav.add(id)
  if (status === 'ecarte') hidden.add(id)
  try {
    localStorage.setItem(KEYS.fav, JSON.stringify([...fav]))
    localStorage.setItem(KEYS.hidden, JSON.stringify([...hidden]))
  } catch {
    /* stockage indisponible : choix non conservé */
  }
}

export function listings(data: StaticData, f: Filters): { items: Property[]; total: number; sources: string[]; defaults: ScoreDefaults } {
  const fav = readSet('fav')
  const hidden = readSet('hidden')
  const today = new Date().toISOString().slice(0, 10)
  const crit = buildCriteria(data.config.criteria, f, data.defaults)
  const q = f.q.trim().toLowerCase()
  const items = data.items
    .map((p) => ({ ...p, status: fav.has(p.id) ? 'favori' : hidden.has(p.id) ? 'ecarte' : 'a_voir' }))
    .filter((p) => {
      const sale = p.custom['vente_le']
      if (typeof sale === 'string' && sale.slice(0, 10) < today) return false
      if (f.favorites ? p.status !== 'favori' : p.status === 'ecarte') return false
      if (q && !`${p.title} ${p.commune ?? ''} ${p.postcode ?? ''} ${p.address ?? ''}`.toLowerCase().includes(q)) return false
      if (f.dept && !(p.postcode ?? '').startsWith(f.dept) && !((p as { insee?: string }).insee ?? '').startsWith(f.dept)) return false
      if (f.type && p.type !== f.type) return false
      const pm = num(f.price_max)
      if (pm != null && !(p.price != null && p.price <= pm)) return false
      for (const [min, v] of [[f.surface_min, p.surface], [f.rooms_min, p.rooms], [f.floor_min, p.floor]] as [string, number | null][]) {
        const m = num(min)
        if (m != null && !(v != null && v >= m)) return false
      }
      const sm = num(f.station_max)
      const walk = p.computed.station_walk_m
      if (sm != null && !(walk != null && walk <= sm * 80)) return false
      if (f.balcony && p.balcony !== true) return false
      if (f.elevator && p.elevator !== true) return false
      if (f.source.length && !f.source.includes(p.source)) return false
      return true
    })
    .map((p) => ({ ...p, ...evaluate(p, crit) }))
  const key: Record<string, (a: Property, b: Property) => number> = {
    price_asc: (a, b) => (a.price ?? Infinity) - (b.price ?? Infinity),
    price_desc: (a, b) => (b.price ?? -Infinity) - (a.price ?? -Infinity),
    ppm2: (a, b) => (a.price_m2 ?? Infinity) - (b.price_m2 ?? Infinity),
    surface: (a, b) => (b.surface ?? -Infinity) - (a.surface ?? -Infinity),
    recent: (a, b) => b.created_at.localeCompare(a.created_at),
    deal: (a, b) => (b.computed.deal_pct ?? -Infinity) - (a.computed.deal_pct ?? -Infinity),
  }
  items.sort(key[f.sort] ?? ((a, b) => b.score - a.score))
  const sources = [...new Set(data.items.map((p) => p.source))].sort()
  return { items: items.slice(0, 400), total: items.length, sources, defaults: data.defaults }
}

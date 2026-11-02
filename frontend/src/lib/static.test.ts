import { describe, expect, it } from 'vitest'
import { emptyFilters } from './filters'
import { buildCriteria, evaluate, fit, listings, type Crit, type StaticData } from './staticApi'
import type { Property } from '../types'

const crit: Crit[] = [
  { key: 'price', label: 'Prix', kind: 'range', field: 'computed.score_price', ideal: [null, 300000], acceptable: [null, 380000], weight: 3 },
  { key: 'surface', label: 'Surface', kind: 'range', field: 'surface', ideal: [55, null], acceptable: [40, null], weight: 3 },
  { key: 'floor', label: 'Étage', kind: 'range', field: 'floor', ideal: [4, 8], acceptable: [2, 12], weight: 2 },
  { key: 'balcony', label: 'Balcon', kind: 'bool', field: 'balcony', weight: 1 },
  { key: 'rooms', label: 'Pièces', kind: 'range', field: 'rooms', weight: 2 },
]
const defaults = { weights: { price: 3, surface: 3, floor: 2, view: 2, station: 1, outdoor: 1, deal: 2 }, budget: 250000, surface: 50, floor: 2 }
const mk = (id: number, o: Partial<Property>): Property => ({ id, title: `bien ${id}`, source: 'encheres', type: 'appartement', price: 200000, surface: 60, rooms: 3, floor: 5,
  balcony: null, elevator: null, status: 'a_voir', tags: [], photos: [], custom: {}, computed: { score_price: 200000 }, created_at: '2026-01-01', kind: 'autre', commune: 'Évry', postcode: '91000', address: null, ...o }) as Property
const data: StaticData = { generated_at: '', config: { departments: [], department_name: '', map: { center: [2, 48], zoom: 9 }, criteria: crit, finance: { rate_pct: 3.8, years: 20, down_payment: 0 }, fees_pct: {} }, defaults,
  items: [mk(1, {}), mk(2, { price: 500000, computed: { score_price: 500000 }, surface: 30 }), mk(3, { balcony: true, floor: 1 })] }

describe('score statique', () => {
  it('fit : plage idéale, bord acceptable, hors plage', () => {
    expect(fit(5, [4, 8], [2, 12])).toBe(1)
    expect(fit(3, [4, 8], [2, 12])).toBe(0.5)
    expect(fit(1, [4, 8], [2, 12])).toBe(0)
  })
  it('les cibles remplacent les plages et les critères hors groupes valent 0', () => {
    const c = buildCriteria(crit, { ...emptyFilters(), budget: '150000', w_price: '5' }, defaults)
    expect(c.find((x) => x.key === 'price')).toMatchObject({ weight: 5, ideal: [null, 150000] })
    expect(c.find((x) => x.key === 'rooms')?.weight).toBe(0)
  })
  it('donnée inconnue = note neutre, pas exclusion', () => {
    const r = evaluate(mk(9, { floor: null, computed: {} }), buildCriteria(crit, emptyFilters(), defaults))
    expect(r.score).toBeGreaterThan(0)
    expect(r.breakdown.find((b) => b.key === 'floor')?.score).toBeNull()
  })
  it('classe par score décroissant et applique les filtres', () => {
    const r = listings(data, emptyFilters())
    expect(r.items[0]?.id).not.toBe(2)
    expect(r.items.at(-1)?.id).toBe(2)
    expect(listings(data, { ...emptyFilters(), balcony: true }).items.map((p) => p.id)).toEqual([3])
    expect(listings(data, { ...emptyFilters(), price_max: '250000' }).total).toBe(2)
  })
  it('masque une enchère dont la date est passée', () => {
    const old = { ...data, items: [mk(5, { custom: { vente_le: '2020-01-01T10:00:00' } })] }
    expect(listings(old, emptyFilters()).total).toBe(0)
  })
})

describe('filtre gare et tri par affaire', () => {
  const withWalk = { ...data, items: [mk(1, { computed: { score_price: 1, station_walk_m: 400, deal_pct: 10 } }), mk(2, { computed: { score_price: 1, station_walk_m: 1600, deal_pct: 40 } }), mk(3, { computed: { score_price: 1 } })] }
  it('gare ≤ 10 min (800 m) exclut les plus loin et les inconnus', () => {
    expect(listings(withWalk, { ...emptyFilters(), station_max: '10' }).items.map((p) => p.id)).toEqual([1])
  })
  it('meilleures affaires : décote décroissante, inconnus en dernier', () => {
    expect(listings(withWalk, { ...emptyFilters(), sort: 'deal' }).items.map((p) => p.id)).toEqual([2, 1, 3])
  })
})

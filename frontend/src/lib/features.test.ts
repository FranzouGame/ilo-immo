import { describe, expect, it } from 'vitest'
import { toCsv } from './csv'
import { cost, monthly } from './finance'
import { isGem, isNew, priceChange } from './kinds'
import type { Property } from '../types'

const base = { kind: 'autre', score: 80, price: 200000, custom: {}, computed: {}, price_history: [], created_at: '2026-01-01', title: 'T3 "Évry"' } as unknown as Property

describe('finance', () => {
  it('mensualité : 200 000 € à 3,8 % sur 20 ans ≈ 1 190 €', () => {
    expect(Math.round(monthly(200000, 3.8, 20))).toBeGreaterThan(1150)
    expect(Math.round(monthly(200000, 3.8, 20))).toBeLessThan(1230)
    expect(monthly(120000, 0, 10)).toBe(1000)
  })
  it('coût : frais selon la catégorie, enchère sur le prix estimé, viager sans coût', () => {
    const fin = { rate_pct: 0, years: 10, down_payment: 20000 }
    const fees = { ancien: 10, enchere: 20 }
    expect(cost(base, fin, fees)).toMatchObject({ base: 200000, fees: 20000, total: 220000, loan: 200000 })
    const auc = { ...base, kind: 'enchere', computed: { auction: { estimate: 100000 } } } as unknown as Property
    expect(cost(auc, fin, fees)).toMatchObject({ base: 100000, fees: 20000 })
    expect(cost({ ...base, kind: 'viager' } as Property, fin, fees)).toBeNull()
  })
})

describe('repères', () => {
  it('pépite : bon score, forte décote, pas occupé, pas accession aidée', () => {
    const gem = { ...base, computed: { deal_pct: 40 } } as unknown as Property
    expect(isGem(gem)).toBe(true)
    expect(isGem({ ...gem, score: 60 } as Property)).toBe(false)
    expect(isGem({ ...gem, kind: 'enchere', custom: { occupation: 'occupé' } } as unknown as Property)).toBe(false)
    expect(isGem({ ...gem, kind: 'aide' } as Property)).toBe(false)
    expect(isGem({ ...gem, kind: 'viager' } as Property)).toBe(false)
    expect(isGem({ ...gem, kind: 'enchere', custom: { occupation: 'libre' } } as unknown as Property)).toBe(true)
  })
  it('variation de prix récente seulement', () => {
    const recent = new Date(Date.now() - 5 * 86400_000).toISOString().slice(0, 10)
    expect(priceChange({ ...base, price: 90000, price_history: [{ date: recent, price: 100000 }] } as Property)).toEqual({ pct: -10, from: 100000 })
    expect(priceChange({ ...base, price: 90000, price_history: [{ date: '2020-01-01', price: 100000 }] } as Property)).toBeNull()
  })
  it('nouveau depuis la dernière visite', () => {
    expect(isNew(base, new Date('2025-12-01').getTime())).toBe(true)
    expect(isNew(base, new Date('2026-02-01').getTime())).toBe(false)
  })
})

describe('csv', () => {
  it('échappe les guillemets et garde les accents', () => {
    expect(toCsv([base])).toContain('"T3 ""Évry"""')
  })
})

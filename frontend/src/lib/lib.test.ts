import { describe, expect, it } from 'vitest'
import type { Property } from '../types'
import { scoreSummary } from './format'
import { priceLines } from './kinds'
import { emptyFilters, eur, fromQuery, sourceLabel, toQuery } from './filters'

describe('filters', () => {
  it('aller-retour query string', () => {
    const f = { ...emptyFilters(), type: 'appartement', price_max: '250000', balcony: true, source: ['encheres', 'interactives'], q: 'évry' }
    expect(fromQuery(toQuery(f))).toEqual(f)
  })
  it('filtres vides -> query vide', () => expect(toQuery(emptyFilters())).toBe(''))
  it('hash invalide ne plante pas', () => expect(fromQuery('#%%%').source).toEqual([]))
})

describe('format', () => {
  it('prix', () => {
    expect(eur(null)).toBe('Prix NC')
    expect(eur(70000)).toContain('70')
  })
  it('source inconnue = son nom', () => expect(sourceLabel('xyz')).toBe('xyz'))
})

describe('affichage par catégorie', () => {
  const base = { price: 70000, price_m2: null, custom: {}, computed: {} } as unknown as Property
  it('une enchère affiche la mise à prix, jamais un prix de vente', () => {
    const p = { ...base, kind: 'enchere', computed: { auction: { estimate: 95000 } } } as unknown as Property
    expect(priceLines(p).main).toContain('Mise à prix')
    expect(priceLines(p).sub).toContain('95')
  })
  it('un viager affiche bouquet et rente', () => {
    const p = { ...base, kind: 'viager', custom: { viager: { bouquet: 55000, rente: 755 } } } as unknown as Property
    expect(priceLines(p).main).toContain('755')
  })
  it('résumé de score', () => {
    expect(scoreSummary([{ label: 'Prix (€)', score: 1 }, { label: 'Surface (m²)', score: 0.1 }, { label: 'x', score: null }])).toBe('+ Prix  - Surface')
  })
})

import { describe, expect, it } from 'vitest'
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

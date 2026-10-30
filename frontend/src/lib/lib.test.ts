import { describe, expect, it } from 'vitest'
import { cone, dirBearing } from './geo'
import { eur, scoreColor } from './format'
import { decodeSpec, encodeSpec, specFromHash, specToHash } from './urlState'

describe('urlState', () => {
  it('aller-retour avec accents', () => {
    const spec = { criteria: { floor: { weight: 4, hard: { min: 3 } } }, q: 'vue dégagée', sort: 'score', order: 'desc' as const }
    expect(decodeSpec(encodeSpec(spec))).toEqual(spec)
    expect(specFromHash(specToHash(spec))).toEqual(spec)
  })
  it('hash invalide -> spec vide', () => {
    expect(specFromHash('#f=%%%').criteria).toEqual({})
  })
})

describe('geo', () => {
  it('cône : sommet + cap vers le nord monte en latitude', () => {
    const c = cone(2.3, 48.6, dirBearing('N'))
    expect(c[0]).toEqual([2.3, 48.6])
    expect(c.slice(1, -1).every(([, lat]) => (lat as number) > 48.6)).toBe(true)
  })
})

describe('format', () => {
  it('formats', () => {
    expect(eur(null)).toBe('-')
    expect(scoreColor(90)).not.toBe(scoreColor(10))
  })
})

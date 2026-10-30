import type { Filters } from '../types'

export const emptyFilters = (): Filters => ({
  q: '', type: '', price_max: '', surface_min: '', rooms_min: '', floor_min: '',
  balcony: false, elevator: false, favorites: false, source: [], sort: 'recent',
})

/** Filtres -> query string de l'API (et de l'URL partageable). Les valeurs vides sont omises. */
export function toQuery(f: Filters): string {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(f)) {
    if (Array.isArray(v)) v.forEach((x) => p.append(k, x))
    else if (v === true) p.set(k, 'true')
    else if (typeof v === 'string' && v !== '' && !(k === 'sort' && v === 'recent')) p.set(k, v)
  }
  return p.toString()
}

export function fromQuery(qs: string): Filters {
  const p = new URLSearchParams(qs.replace(/^#/, ''))
  const f = emptyFilters()
  for (const k of Object.keys(f) as (keyof Filters)[]) {
    if (k === 'source') f.source = p.getAll('source')
    else if (typeof f[k] === 'boolean') (f[k] as boolean) = p.get(k) === 'true'
    else if (p.has(k)) (f[k] as string) = p.get(k) ?? ''
  }
  return f
}

export const eur = (v: number | null | undefined): string => (v == null ? 'Prix NC' : `${Math.round(v).toLocaleString('fr-FR')} €`)
export const photoUrl = (f: string): string => (f.startsWith('http') ? f : `/api/photos/${f}`)
export const SOURCES: Record<string, string> = {
  encheres: 'Enchère judiciaire', interactives: 'Vente interactive', manuel: 'Ajouté par moi', demo: 'Démo',
}
export const sourceLabel = (s: string): string => SOURCES[s] ?? s

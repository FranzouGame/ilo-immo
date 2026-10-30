import type { Filters } from '../types'

export const emptyFilters = (): Filters => ({
  q: '', dept: '', type: '', price_max: '', surface_min: '', rooms_min: '', floor_min: '',
  balcony: false, elevator: false, favorites: false, source: [], sort: 'score',
  budget: '', surface_target: '', floor_target: '',
  w_price: '', w_surface: '', w_floor: '', w_view: '', w_station: '', w_outdoor: '', w_deal: '',
})

/** Filtres -> query string de l'API (et de l'URL partageable). Les valeurs vides ou par défaut sont omises. */
export function toQuery(f: Filters): string {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(f)) {
    if (Array.isArray(v)) v.forEach((x) => p.append(k, x))
    else if (v === true) p.set(k, 'true')
    else if (typeof v === 'string' && v !== '' && !(k === 'sort' && v === 'score')) p.set(k, v)
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
  encheres: 'Enchères judiciaires', interactives: 'Ventes interactives', viager: 'Viager', programmes: 'Neuf et accession aidée',
  manuel: 'Ajoutées par moi', demo: 'Démo',
}
export const sourceLabel = (s: string): string => SOURCES[s] ?? s

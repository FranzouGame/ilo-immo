import type { Property } from '../types'

const cell = (v: unknown): string => `"${String(v ?? '').replace(/"/g, '""')}"`

/** Export CSV (séparateur « ; », ouvrable dans Excel) des annonces affichées. */
export function toCsv(items: Property[]): string {
  const head = ['Score', 'Titre', 'Catégorie', 'Type', 'Prix', 'Surface', 'Pièces', 'Étage', 'Commune', 'Code postal', 'Décote estimée %', 'Lien']
  const rows = items.map((p) => [p.score, p.title, p.kind, p.type, p.price, p.surface, p.rooms, p.floor, p.commune, p.postcode, p.computed.deal_pct, p.url])
  return '﻿' + [head, ...rows].map((r) => r.map(cell).join(';')).join('\n')
}

export function downloadCsv(items: Property[]): void {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([toCsv(items)], { type: 'text/csv;charset=utf-8' }))
  a.download = 'annonces.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

export const eur = (v: number | null | undefined): string => (v == null ? '-' : `${Math.round(v).toLocaleString('fr-FR')} €`)
export const num = (v: number | null | undefined, unit = ''): string => (v == null ? '-' : `${v}${unit}`)
export const scoreColor = (s: number | undefined): string =>
  s == null ? '#888' : s >= 75 ? '#1b9e5a' : s >= 55 ? '#e0a100' : s >= 35 ? '#e06b00' : '#c0392b'

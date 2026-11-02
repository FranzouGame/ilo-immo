import { eur } from '../lib/filters'
import { cost, type Fees, type Finance } from '../lib/finance'
import { kindLabel, priceLines } from '../lib/kinds'
import type { Property } from '../types'

const rows: { k: string; f: (p: Property, fin: Finance, fees: Fees) => string }[] = [
  { k: 'Catégorie', f: (p) => kindLabel(p) },
  { k: 'Prix', f: (p) => priceLines(p).main },
  { k: 'Estimation / détail', f: (p) => priceLines(p).sub ?? '-' },
  { k: 'Score', f: (p) => `${p.score}/100` },
  { k: 'Écart vs valeur', f: (p) => (p.computed.deal_pct != null ? `-${p.computed.deal_pct} %` : '-') },
  { k: 'Surface', f: (p) => (p.surface ? `${Math.round(p.surface)} m²` : '-') },
  { k: 'Pièces', f: (p) => String(p.rooms ?? '-') },
  { k: 'Étage', f: (p) => (p.floor != null ? String(p.floor) : '-') },
  { k: 'Balcon / terrasse', f: (p) => (p.balcony ? 'oui' : '-') },
  { k: 'DPE', f: (p) => p.dpe ?? '-' },
  { k: 'Gare à pied', f: (p) => (p.computed.station_walk_m != null ? `${Math.round(p.computed.station_walk_m / 80)} min` : '-') },
  { k: 'Mensualité estimée', f: (p, fin, fees) => { const c = cost(p, fin, fees); return c ? `${eur(c.monthly)}/mois` : '-' } },
  { k: 'Lieu', f: (p) => `${p.commune ?? ''} ${p.postcode ?? ''}` },
]

export default function Compare({ items, fin, fees, onClose }: { items: Property[]; fin: Finance; fees: Fees; onClose: () => void }) {
  return (
    <div className="modal" onClick={onClose}><div className="dialog big" onClick={(e) => e.stopPropagation()}>
      <button className="close" onClick={onClose} aria-label="Fermer">✕</button>
      <h2>Comparer</h2>
      <div className="scroll"><table className="cmptable"><thead><tr><th />{items.map((p) => <th key={p.id}>{p.title}{p.url && <><br /><a href={p.url} target="_blank" rel="noreferrer">annonce ↗</a></>}</th>)}</tr></thead>
        <tbody>{rows.map((r) => <tr key={r.k}><th>{r.k}</th>{items.map((p) => <td key={p.id}>{r.f(p, fin, fees)}</td>)}</tr>)}</tbody></table></div>
    </div></div>
  )
}

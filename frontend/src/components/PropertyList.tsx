import { eur, scoreColor } from '../lib/format'
import type { Property } from '../types'

interface Props {
  items: Property[]
  selected: number | null
  onSelect: (id: number) => void
  sort: string
  setSort: (s: string) => void
}

export default function PropertyList({ items, selected, onSelect, sort, setSort }: Props) {
  return (
    <section className="list">
      <div className="row">
        <label>Trier par <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="score">Score</option><option value="price">Prix</option><option value="price_m2">Prix/m²</option>
          <option value="surface">Surface</option><option value="updated_at">Récents</option>
        </select></label>
      </div>
      {items.length === 0 && <p className="hint">Aucun bien. Ajoutez-en un (bouton « + Ajouter ») ou lancez <code>make seed</code> pour la démo.</p>}
      {items.map((p) => (
        <article key={p.id} className={`card ${selected === p.id ? 'sel' : ''}`} onClick={() => onSelect(p.id)}>
          <div className="score" style={{ background: scoreColor(p.score) }} title={p.near ? 'Quasi éligible' : undefined}>{p.score ?? '-'}{p.near ? '≈' : ''}</div>
          <div className="body">
            <strong>{p.title || p.address || `Bien ${p.id}`}</strong>
            <span>{p.commune ?? ''} · {p.type} · {p.surface ?? '?'} m² · {p.rooms ?? '?'} p · ét. {p.floor ?? '?'}/{p.floors_total ?? '?'}</span>
            <span>{eur(p.price)} {p.price_m2 ? `(${p.price_m2} €/m²)` : ''} {p.computed.market_gap_pct != null && <em>{p.computed.market_gap_pct > 0 ? '+' : ''}{p.computed.market_gap_pct}% vs marché</em>}</span>
            <span className="tags">{p.status !== 'a_voir' && <b>{p.status}</b>} {p.tags.map((t) => `#${t}`).join(' ')}</span>
          </div>
        </article>
      ))}
    </section>
  )
}

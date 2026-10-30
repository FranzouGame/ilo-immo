import { photoUrl } from '../lib/filters'
import { scoreColor, scoreSummary } from '../lib/format'
import { kindLabel, kindOf, priceLines, whenLabel } from '../lib/kinds'
import type { Property } from '../types'

const isNew = (p: Property): boolean => Date.now() - new Date(p.created_at).getTime() < 3 * 86400_000

export default function ListingCard({ p, onOpen, onFav }: { p: Property; onOpen: () => void; onFav: () => void }) {
  const facts = [p.rooms ? `${p.rooms} p.` : null, p.surface ? `${Math.round(p.surface)} m²` : null,
    p.floor != null ? (p.floor === 0 ? 'RDC' : `étage ${p.floor}`) : null].filter(Boolean).join(' · ')
  const price = priceLines(p)
  const when = whenLabel(p)
  return (
    <article className="lcard" onClick={onOpen}>
      <div className="photo" style={p.photos[0] ? { backgroundImage: `url(${photoUrl(p.photos[0])})` } : undefined}>
        {!p.photos[0] && <span>{kindOf(p).icon}</span>}
        <span className="badge" title={kindOf(p).blurb}>{kindOf(p).icon} {kindLabel(p)}</span>
        {isNew(p) && <span className="badge new">Nouveau</span>}
        <button className={p.status === 'favori' ? 'fav on' : 'fav'} aria-label="Favori" onClick={(e) => { e.stopPropagation(); onFav() }}>★</button>
        <span className="score" style={{ background: scoreColor(p.score) }} title={scoreSummary(p.breakdown) || 'Score selon vos préférences'}>{p.score}</span>
      </div>
      <div className="info">
        <b className="price">{price.main}</b>
        {price.sub && <div className="line sub">{price.sub}</div>}
        <div className="line">{p.type === 'maison' ? 'Maison' : 'Appartement'} · {facts || 'détails à voir'}</div>
        <div className="line muted">{p.commune ?? p.address ?? ''} {p.postcode ? `(${p.postcode})` : ''}</div>
        {when && <div className="line when">📅 {when}</div>}
        <div className="line">{p.balcony && <span className="tag">Balcon/terrasse</span>}{p.elevator && <span className="tag">Ascenseur</span>}{p.dpe && <span className="tag">DPE {p.dpe}</span>}</div>
      </div>
    </article>
  )
}

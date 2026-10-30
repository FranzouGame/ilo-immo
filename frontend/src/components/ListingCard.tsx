import { eur, photoUrl, sourceLabel } from '../lib/filters'
import type { Property } from '../types'

const isNew = (p: Property): boolean => Date.now() - new Date(p.created_at).getTime() < 3 * 86400_000

export default function ListingCard({ p, onOpen, onFav }: { p: Property; onOpen: () => void; onFav: () => void }) {
  const facts = [p.rooms ? `${p.rooms} p.` : null, p.surface ? `${Math.round(p.surface)} m²` : null,
    p.floor != null ? (p.floor === 0 ? 'RDC' : `étage ${p.floor}`) : null].filter(Boolean).join(' · ')
  return (
    <article className="lcard" onClick={onOpen}>
      <div className="photo" style={p.photos[0] ? { backgroundImage: `url(${photoUrl(p.photos[0])})` } : undefined}>
        {!p.photos[0] && <span>{p.type === 'maison' ? '🏠' : '🏢'}</span>}
        <span className="badge">{sourceLabel(p.source)}</span>
        {isNew(p) && <span className="badge new">Nouveau</span>}
        <button className={p.status === 'favori' ? 'fav on' : 'fav'} aria-label="Favori" onClick={(e) => { e.stopPropagation(); onFav() }}>★</button>
      </div>
      <div className="info">
        <b className="price">{eur(p.price)}</b>{p.price_m2 ? <small> · {p.price_m2.toLocaleString('fr-FR')} €/m²</small> : null}
        <div className="line">{p.type === 'maison' ? 'Maison' : 'Appartement'} · {facts || 'détails à voir'}</div>
        <div className="line muted">{p.commune ?? p.address ?? ''} {p.postcode ? `(${p.postcode})` : ''}</div>
        <div className="line">{p.balcony && <span className="tag">Balcon/terrasse</span>}{p.elevator && <span className="tag">Ascenseur</span>}{p.dpe && <span className="tag">DPE {p.dpe}</span>}</div>
      </div>
    </article>
  )
}

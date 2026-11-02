import { photoUrl } from '../lib/filters'
import { cost, type Fees, type Finance } from '../lib/finance'
import { scoreColor, scoreSummary } from '../lib/format'
import { flags, isGem, isNew, kindLabel, kindOf, priceChange, priceLines, whenLabel } from '../lib/kinds'
import type { Property } from '../types'

interface Props {
  p: Property
  lastVisit: number | null
  fin: Finance
  fees: Fees
  compared: boolean
  onOpen: () => void
  onFav: () => void
  onCompare: () => void
}

export default function ListingCard({ p, lastVisit, fin, fees, compared, onOpen, onFav, onCompare }: Props) {
  const facts = [p.rooms ? `${p.rooms} p.` : null, p.surface ? `${Math.round(p.surface)} m²` : null,
    p.floor != null ? (p.floor === 0 ? 'RDC' : `étage ${p.floor}`) : null].filter(Boolean).join(' · ')
  const price = priceLines(p)
  const when = whenLabel(p)
  const change = priceChange(p)
  const c = cost(p, fin, fees)
  const deal = p.computed.deal_pct
  const walk = p.computed.station_walk_m
  return (
    <article className="lcard" onClick={onOpen}>
      <div className={p.photos[0] ? 'photo' : 'photo nophoto'} style={p.photos[0] ? { backgroundImage: `url(${photoUrl(p.photos[0])})` } : undefined}>
        {!p.photos[0] && <span>{kindOf(p).icon}</span>}
        <span className="badge" title={kindOf(p).blurb}>{kindOf(p).icon} {kindLabel(p)}</span>
        {isGem(p) && <span className="badge gem" title="Bon score et forte décote apparente (voir « Comprendre les ventes »)">💎 Pépite</span>}
        {!isGem(p) && isNew(p, lastVisit) && <span className="badge new">Nouveau</span>}
        <button className={p.status === 'favori' ? 'fav on' : 'fav'} aria-label="Favori" onClick={(e) => { e.stopPropagation(); onFav() }}>★</button>
        <span className="score" style={{ background: scoreColor(p.score) }} title={scoreSummary(p.breakdown) || 'Score selon vos préférences'}>{p.score}</span>
      </div>
      <div className="info">
        <b className="price">{price.main}</b>
        {change && <span className={change.pct < 0 ? 'chg down' : 'chg up'} title={`Ancien prix : ${Math.round(change.from).toLocaleString('fr-FR')} €`}>{change.pct < 0 ? '↓' : '↑'} {Math.abs(change.pct)} %</span>}
        {price.sub && <div className="line sub">{price.sub}</div>}
        <div className="line">{p.type === 'maison' ? 'Maison' : 'Appartement'} · {facts || 'détails à voir'}</div>
        <div className="line muted">{p.commune ?? p.address ?? ''} {p.postcode ? `(${p.postcode})` : ''}{walk != null ? ` · gare ≈ ${Math.max(1, Math.round(walk / 80))} min à pied` : ''}</div>
        {when && <div className="line when">📅 {when}</div>}
        <div className="line">
          {flags(p).map((f) => <span key={f.text} className={`tag ${f.tone}`}>{f.tone === 'warn' ? '⚠ ' : '✓ '}{f.text}</span>)}
          {deal != null && deal >= 10 && p.kind !== 'aide' && <span className="tag deal" title="Écart estimé avec la valeur du secteur ou la valeur libre">-{deal} % {p.kind === 'viager' ? 'décote' : p.kind === 'enchere' ? 'estimé vs valeur' : 'vs marché'}</span>}
          {p.balcony && <span className="tag">Balcon/terrasse</span>}{p.elevator && <span className="tag">Ascenseur</span>}{p.dpe && <span className="tag">DPE {p.dpe}</span>}
        </div>
        <div className="line cardfoot">
          <span className="muted">{c && c.monthly > 0 ? `≈ ${c.monthly.toLocaleString('fr-FR')} €/mois` : ''}</span>
          <label className="cmp" onClick={(e) => e.stopPropagation()}><input type="checkbox" checked={compared} onChange={onCompare} /> Comparer</label>
        </div>
      </div>
    </article>
  )
}

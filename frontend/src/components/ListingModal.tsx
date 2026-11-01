import { useState } from 'react'
import { api } from '../api'
import { photoUrl, sourceLabel } from '../lib/filters'
import { scoreColor } from '../lib/format'
import { kindLabel, priceLines } from '../lib/kinds'
import InfoBox from './InfoBox'
import type { Property } from '../types'

interface Props { p: Property; onClose: () => void; onChanged: () => void; openGuide: (id: string) => void; setStatus: (s: string) => void; canDelete: boolean }

const Fact = ({ k, v }: { k: string; v: React.ReactNode }) => (v == null || v === '' ? null : <div className="fact"><span>{k}</span><b>{v}</b></div>)

export default function ListingModal({ p, onClose, onChanged, openGuide, setStatus, canDelete }: Props) {
  const [img, setImg] = useState(0)
  const c = p.computed
  const price = priceLines(p)
  return (
    <div className="modal" onClick={onClose}><div className="dialog big" onClick={(e) => e.stopPropagation()}>
      <button className="close" onClick={onClose} aria-label="Fermer">✕</button>
      {p.photos.length > 0 && (
        <div className="gallery">
          <img src={photoUrl(p.photos[img] ?? p.photos[0] ?? '')} alt="" />
          <div className="thumbs">{p.photos.map((f, i) => <img key={f} src={photoUrl(f)} alt="" className={i === img ? 'on' : ''} onClick={() => setImg(i)} />)}</div>
        </div>
      )}
      <h2>{p.title || `${p.type} à ${p.commune}`}</h2>
      <p className="price big">{price.main}</p>
      {price.sub && <p className="sub">{price.sub}</p>}
      <p className="muted">{kindLabel(p)} · {p.address} · Source : {sourceLabel(p.source)}</p>
      <div className="scorebox"><span className="score big" style={{ background: scoreColor(p.score) }}>{p.score}</span>
        <details><summary>Pourquoi ce score ? <small>(selon vos préférences)</small></summary>
          {p.breakdown.map((b) => <div key={b.key} className="bar"><span>{b.label}{b.manual ? ' (saisie)' : ''}{b.score == null ? ' - inconnu' : ''}</span>
            <i style={{ width: `${(b.score ?? 0.5) * 100}%`, background: b.score == null ? '#999' : scoreColor((b.score ?? 0) * 100) }} /></div>)}
        </details></div>
      <InfoBox p={p} openGuide={openGuide} />
      <div className="facts">
        <Fact k="Surface" v={p.surface ? `${p.surface} m²` : null} /><Fact k="Pièces" v={p.rooms} />
        <Fact k="Étage" v={p.floor != null ? `${p.floor}${p.floors_total ? ` / ${p.floors_total}` : ''}` : null} />
        <Fact k="Balcon / terrasse" v={p.balcony ? 'Oui' : null} /><Fact k="Ascenseur" v={p.elevator ? 'Oui' : null} />
        <Fact k="DPE" v={p.dpe} /><Fact k="Construit en" v={p.year_built} /><Fact k="Orientation" v={p.orientation} />
      </div>
      {p.notes && <p className="note">{p.notes}</p>}
      {(c.vis_a_vis || c.view_quality || c.station_walk_m != null || c.market_gap_pct != null) && (
        <details><summary>Quartier et vue (estimations)</summary>
          <ul>
            {c.vis_a_vis && <li>Vis-à-vis : {c.vis_a_vis.explanation}</li>}
            {c.view_quality && <li>Vue : {c.view_quality.score}/100 {c.view_quality.reasons.join(' · ')}</li>}
            {c.station_walk_m != null && <li>Gare à pied : ≈ {c.station_walk_m} m</li>}
            {c.market_gap_pct != null && c.market_ref && <li>Prix vs ventes réelles du secteur ({Math.round(c.market_ref.median_ppm2)} €/m²) : {c.market_gap_pct > 0 ? '+' : ''}{c.market_gap_pct} %</li>}
            {c.georisks && <li>Risques : {c.georisks.items.join(', ') || 'aucun recensé'}</li>}
          </ul></details>
      )}
      <div className="row">
        {p.url && <a className="btn primary" href={p.url} target="_blank" rel="noreferrer">Voir l'annonce d'origine ↗</a>}
        <button onClick={() => setStatus(p.status === 'favori' ? 'a_voir' : 'favori')}>{p.status === 'favori' ? '★ Retirer des favoris' : '☆ Favori'}</button>
        <button onClick={() => { setStatus('ecarte'); onClose() }}>Masquer</button>
        {canDelete && <button className="danger" onClick={() => { if (confirm('Supprimer cette annonce ?')) void api(`/properties/${p.id}`, undefined, 'DELETE').then(() => { onChanged(); onClose() }) }}>Supprimer</button>}
      </div>
    </div></div>
  )
}

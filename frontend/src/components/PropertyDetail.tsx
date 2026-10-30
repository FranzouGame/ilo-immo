import { useEffect, useState } from 'react'
import { api, upload } from '../api'
import { DIRECTIONS, earthUrl, mapillaryUrl, streetViewUrl } from '../lib/geo'
import { eur, scoreColor } from '../lib/format'
import type { Property } from '../types'

interface Props {
  id: number
  onClose: () => void
  onChanged: () => void
  onLoaded: (p: Property) => void
  mode3d: boolean
  setMode3d: (b: boolean) => void
  direction: string
  setDirection: (d: string) => void
  score?: Property
}

const Slider = ({ label, value, onChange }: { label: string; value: number | null; onChange: (v: number | null) => void }) => (
  <label className="slider">{label}: <b>{value ?? 'non noté'}</b>
    <input type="range" min={0} max={10} value={value ?? 5} onChange={(e) => onChange(Number(e.target.value))} />
    {value != null && <button className="link" onClick={() => onChange(null)}>effacer</button>}
  </label>
)

export default function PropertyDetail({ id, onClose, onChanged, onLoaded, mode3d, setMode3d, direction, setDirection, score }: Props) {
  const [p, setP] = useState<Property | null>(null)
  const [tag, setTag] = useState('')
  useEffect(() => {
    void api<Property>(`/properties/${id}`).then((d) => { setP(d); onLoaded(d); if (d.orientation) setDirection(d.orientation) })
  }, [id]) // eslint-disable-line react-hooks/exhaustive-deps
  if (!p) return <aside className="detail">Chargement…</aside>
  const patch = async (body: Record<string, unknown>) => {
    const d = await api<Property>(`/properties/${id}`, body, 'PATCH')
    setP({ ...p, ...d })
    onChanged()
  }
  const c = p.computed
  const s = score?.score
  return (
    <aside className="detail">
      <button className="close" onClick={onClose} aria-label="Fermer">✕</button>
      <h2>{p.title || p.address || `Bien ${p.id}`}</h2>
      <p>{p.address} {p.commune} · {eur(p.price)} · {p.surface} m² · {p.type}</p>
      {s != null && <div className="bigscore" style={{ background: scoreColor(s) }}>{s}/100</div>}
      {p.url && <a href={p.url} target="_blank" rel="noreferrer">Annonce source ↗</a>}

      <h3>Vue et vis-à-vis</h3>
      {!c.has_buildings && <p className="warn">Bâtiments BD TOPO absents autour du bien : vis-à-vis et ciel non calculés (<code>make ingest SRC=ign_bdtopo</code>).</p>}
      {c.vis_a_vis && <p><b>Vis-à-vis {c.vis_a_vis.score}/100</b> - {c.vis_a_vis.explanation}</p>}
      {c.view_quality && <p><b>Qualité de vue {c.view_quality.score}/100</b><br />{c.view_quality.reasons.join(' · ') || 'aucun élément remarquable'}</p>}
      <p>Fenêtre ≈ {c.window_altitude_m ?? '?'} m d'altitude · étage relatif {c.relative_floor ?? '?'} · ciel visible {c.sky_index ?? '?'}/100</p>
      {c.sectors && (
        <div className="sectors">
          {DIRECTIONS.map((d) => {
            const sec = c.sectors?.[d]
            return <div key={d} className={d === direction ? 'sec on' : 'sec'} title={sec?.open ? 'dégagé' : `+${sec?.floors_above} étage(s)`}>
              <b>{d}</b><span>{sec?.open ? '≥' : ''}{sec?.distance_m} m</span></div>
          })}
        </div>
      )}
      <div className="row">
        <select value={direction} onChange={(e) => setDirection(e.target.value)}>{DIRECTIONS.map((d) => <option key={d}>{d}</option>)}</select>
        <button className="primary" onClick={() => setMode3d(!mode3d)}>{mode3d ? 'Retour 2D' : 'Voir en 3D'}</button>
      </div>
      {p.lat != null && p.lon != null && (
        <p className="links"><a href={streetViewUrl(p.lat, p.lon)} target="_blank" rel="noreferrer">Street View ↗</a> <a href={mapillaryUrl(p.lat, p.lon)} target="_blank" rel="noreferrer">Mapillary ↗</a> <a href={earthUrl(p.lat, p.lon)} target="_blank" rel="noreferrer">Google Earth ↗</a></p>
      )}

      <h3>Ma visite (pèse plus que l'estimation)</h3>
      <Slider label="Vue" value={p.manual_view} onChange={(v) => void patch({ manual_view: v })} />
      <Slider label="Luminosité" value={p.manual_light} onChange={(v) => void patch({ manual_light: v })} />
      <Slider label="Absence de vis-à-vis" value={p.manual_vis_a_vis} onChange={(v) => void patch({ manual_vis_a_vis: v })} />
      <label className="row">Façade principale
        <select value={p.orientation ?? ''} onChange={(e) => void patch({ orientation: e.target.value || null })}>
          <option value="">inconnue</option>{DIRECTIONS.map((d) => <option key={d}>{d}</option>)}</select></label>
      <div className="photos">{p.photos.map((f) => <img key={f} src={`/api/photos/${f}`} alt="" />)}</div>
      <input type="file" accept="image/*" onChange={(e) => { const f = e.target.files?.[0]; if (f) void upload<Property>(`/properties/${id}/photos`, f).then((d) => setP({ ...p, photos: d.photos })) }} />

      <h3>Marché, énergie, risques, transports</h3>
      <ul>
        <li>Prix/m² : {p.price_m2 ?? '?'} € · référence {c.market_ref ? `${Math.round(c.market_ref.median_ppm2)} € (${c.market_ref.scope === 'cell' ? 'quartier 1 km' : 'commune'}, ${c.market_ref.n} ventes)` : 'indisponible (import DVF ?)'} {c.market_gap_pct != null && <b>({c.market_gap_pct > 0 ? '+' : ''}{c.market_gap_pct}%)</b>}</li>
        <li>DPE {p.dpe ?? '?'} / GES {p.ges ?? '?'} · construit en {p.year_built ?? '?'}</li>
        <li>Risques : {c.georisks ? (c.georisks.items.join(', ') || 'aucun recensé') : 'non calculés'}</li>
        <li>Gare à pied ≈ {c.station_walk_m ?? '?'} m · bruit estimé {c.noise_score ?? '?'}/100 · espaces verts {c.parks_count ?? '?'}</li>
      </ul>
      {p.neighbor_sales && p.neighbor_sales.length > 0 && (
        <table><thead><tr><th>Date</th><th>Prix</th><th>m²</th><th>€/m²</th><th>Dist.</th></tr></thead><tbody>
          {p.neighbor_sales.map((v, i) => <tr key={i}><td>{v.sold_on}</td><td>{eur(v.price)}</td><td>{v.surface}</td><td>{Math.round(v.price_m2)}</td><td>{Math.round(v.dist)} m</td></tr>)}
        </tbody></table>
      )}

      {score?.breakdown && (<>
        <h3>Détail du score</h3>
        {score.breakdown.map((b) => <div key={b.key} className="bar" title={String(b.value)}>
          <span>{b.label}{b.manual ? ' (saisie)' : ''}</span><i style={{ width: `${(b.score ?? 0.5) * 100}%`, background: b.score == null ? '#999' : scoreColor((b.score ?? 0) * 100) }} /></div>)}
      </>)}

      <h3>Suivi</h3>
      <div className="row">
        <select value={p.status} onChange={(e) => void patch({ status: e.target.value })}>
          {['a_voir', 'favori', 'visite', 'ecarte'].map((x) => <option key={x}>{x}</option>)}</select>
        <button className="danger" onClick={() => { if (confirm('Supprimer ce bien ?')) void api(`/properties/${id}`, undefined, 'DELETE').then(() => { onChanged(); onClose() }) }}>Supprimer</button>
      </div>
      <div className="chips">{p.tags.map((t) => <button key={t} className="chip on" onClick={() => void patch({ tags: p.tags.filter((x) => x !== t) })}>#{t} ✕</button>)}
        <input className="narrow" placeholder="+ tag" value={tag} onChange={(e) => setTag(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && tag) { void patch({ tags: [...p.tags, tag] }); setTag('') } }} /></div>
      <textarea placeholder="Notes" defaultValue={p.notes} onBlur={(e) => { if (e.target.value !== p.notes) void patch({ notes: e.target.value }) }} />
    </aside>
  )
}

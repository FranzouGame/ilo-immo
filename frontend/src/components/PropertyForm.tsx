import { useState } from 'react'
import { api } from '../api'
import type { Computed, Property } from '../types'

type Draft = Partial<Property> & { postcode?: string; insee?: string; computed?: Computed; georisks_error?: string }

export default function PropertyForm({ onClose, onCreated }: { onClose: () => void; onCreated: (id: number) => void }) {
  const [d, setD] = useState<Draft>({ type: 'appartement' })
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setD((x) => ({ ...x, [k]: v }))
  const num = (v: string): number | null => (v === '' ? null : Number(v))

  const prefill = async () => {
    setBusy(true)
    setMsg('')
    try {
      const r = await api<Draft>('/properties/prefill', { address: d.address, type: d.type, surface: d.surface, price: d.price, floor: d.floor, orientation: d.orientation })
      const { computed, ...rest } = r
      setD((x) => ({ ...x, ...rest }))
      setMsg(`Pré-rempli : ${computed?.market_ref ? `prix secteur ${Math.round(computed.market_ref.median_ppm2)} €/m²` : 'prix secteur indisponible'}, `
        + `vis-à-vis ${computed?.vis_a_vis?.score ?? 'non calculé'}, qualité de vue ${computed?.view_quality?.score ?? '?'}.`)
    } catch (e) {
      setMsg((e as Error).message)
    }
    setBusy(false)
  }
  const create = async () => {
    const { ...body } = d
    const r = await api<Property>('/properties', body)
    onCreated(r.id)
  }
  return (
    <div className="modal"><div className="dialog">
      <h2>Ajouter un bien</h2>
      <label>URL de la source <input value={d.url ?? ''} onChange={(e) => set('url', e.target.value)} placeholder="notaire, enchère, bailleur…" /></label>
      <label>Titre <input value={d.title ?? ''} onChange={(e) => set('title', e.target.value)} /></label>
      <label>Adresse <div className="row"><input value={d.address ?? ''} onChange={(e) => set('address', e.target.value)} placeholder="12 rue … 91000 Évry" />
        <button disabled={!d.address || busy} onClick={() => void prefill()}>Pré-remplir</button></div></label>
      {msg && <p className="hint">{msg}</p>}
      <div className="grid">
        <label>Type <select value={d.type} onChange={(e) => set('type', e.target.value)}><option>appartement</option><option>maison</option></select></label>
        <label>Prix € <input type="number" value={d.price ?? ''} onChange={(e) => set('price', num(e.target.value))} /></label>
        <label>Surface m² <input type="number" value={d.surface ?? ''} onChange={(e) => set('surface', num(e.target.value))} /></label>
        <label>Pièces <input type="number" value={d.rooms ?? ''} onChange={(e) => set('rooms', num(e.target.value))} /></label>
        <label>Étage <input type="number" value={d.floor ?? ''} onChange={(e) => set('floor', num(e.target.value))} /></label>
        <label>Étages immeuble <input type="number" value={d.floors_total ?? ''} onChange={(e) => set('floors_total', num(e.target.value))} /></label>
        <label>Orientation <select value={d.orientation ?? ''} onChange={(e) => set('orientation', e.target.value || null)}><option value="">?</option>
          {['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'].map((o) => <option key={o}>{o}</option>)}</select></label>
        <label>État <select value={d.condition ?? ''} onChange={(e) => set('condition', e.target.value || null)}><option value="">?</option><option value="a_renover">à rénover</option><option value="bon">bon</option><option value="neuf">neuf</option></select></label>
        <label><input type="checkbox" checked={!!d.balcony} onChange={(e) => set('balcony', e.target.checked)} /> Balcon/terrasse</label>
        <label><input type="checkbox" checked={!!d.elevator} onChange={(e) => set('elevator', e.target.checked)} /> Ascenseur</label>
      </div>
      <div className="row"><button onClick={onClose}>Annuler</button><button className="primary" onClick={() => void create()}>Enregistrer</button></div>
    </div></div>
  )
}

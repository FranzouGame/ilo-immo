import { useState } from 'react'
import { api } from '../api'

interface Draft { url: string; title: string; address: string; type: string; price: string; surface: string; rooms: string; floor: string; balcony: boolean; elevator: boolean }
const empty: Draft = { url: '', title: '', address: '', type: 'appartement', price: '', surface: '', rooms: '', floor: '', balcony: false, elevator: false }
const n = (v: string): number | null => (v === '' ? null : Number(v))

export default function AddForm({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [d, setD] = useState<Draft>(empty)
  const [err, setErr] = useState('')
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setD((x) => ({ ...x, [k]: v }))
  const save = async () => {
    try {
      await api('/properties', { url: d.url || null, title: d.title, address: d.address || null, type: d.type, price: n(d.price), surface: n(d.surface),
        rooms: n(d.rooms), floor: n(d.floor), balcony: d.balcony || null, elevator: d.elevator || null })
      onCreated()
    } catch (e) {
      setErr((e as Error).message)
    }
  }
  return (
    <div className="modal" onClick={onClose}><div className="dialog" onClick={(e) => e.stopPropagation()}>
      <h2>Ajouter une annonce</h2>
      <label>Lien de l'annonce <input value={d.url} onChange={(e) => set('url', e.target.value)} placeholder="https://…" /></label>
      <label>Titre <input value={d.title} onChange={(e) => set('title', e.target.value)} /></label>
      <label>Adresse (placée sur la carte automatiquement) <input value={d.address} onChange={(e) => set('address', e.target.value)} placeholder="12 rue … 91000 Évry" /></label>
      <div className="grid">
        <label>Type <select value={d.type} onChange={(e) => set('type', e.target.value)}><option value="appartement">Appartement</option><option value="maison">Maison</option></select></label>
        <label>Prix (€) <input type="number" value={d.price} onChange={(e) => set('price', e.target.value)} /></label>
        <label>Surface (m²) <input type="number" value={d.surface} onChange={(e) => set('surface', e.target.value)} /></label>
        <label>Pièces <input type="number" value={d.rooms} onChange={(e) => set('rooms', e.target.value)} /></label>
        <label>Étage <input type="number" value={d.floor} onChange={(e) => set('floor', e.target.value)} /></label>
        <label className="chk"><input type="checkbox" checked={d.balcony} onChange={(e) => set('balcony', e.target.checked)} /> Balcon / terrasse</label>
        <label className="chk"><input type="checkbox" checked={d.elevator} onChange={(e) => set('elevator', e.target.checked)} /> Ascenseur</label>
      </div>
      {err && <p className="err">{err}</p>}
      <div className="row"><button onClick={onClose}>Annuler</button><button className="primary" onClick={() => void save()}>Ajouter</button></div>
    </div></div>
  )
}

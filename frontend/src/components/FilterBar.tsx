import type { Filters } from '../types'
import { sourceLabel } from '../lib/filters'

interface Props { departments: { code: string; name: string }[]; f: Filters; set: (f: Filters) => void; sources: string[]; reset: () => void }

const Num = ({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder: string }) => (
  <label className="fld">{label}<input type="number" min={0} inputMode="numeric" value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} /></label>
)

export default function FilterBar({ departments, f, set, sources, reset }: Props) {
  const up = <K extends keyof Filters>(k: K, v: Filters[K]) => set({ ...f, [k]: v })
  return (
    <section className="filterbar">
      <label className="fld wide">Où ?<input placeholder="Commune ou code postal" value={f.q} onChange={(e) => up('q', e.target.value)} /></label>
      {departments.length > 1 && (
        <label className="fld">Département
          <select value={f.dept} onChange={(e) => up('dept', e.target.value)}>
            <option value="">Tous</option>{departments.map((d) => <option key={d.code} value={d.code}>{d.name} ({d.code})</option>)}
          </select></label>
      )}
      <label className="fld">Type
        <select value={f.type} onChange={(e) => up('type', e.target.value)}>
          <option value="">Tous</option><option value="appartement">Appartement</option><option value="maison">Maison</option>
        </select></label>
      <Num label="Prix max (€)" value={f.price_max} placeholder="Illimité" onChange={(v) => up('price_max', v)} />
      <Num label="Surface min (m²)" value={f.surface_min} placeholder="Toutes" onChange={(v) => up('surface_min', v)} />
      <Num label="Pièces min" value={f.rooms_min} placeholder="Toutes" onChange={(v) => up('rooms_min', v)} />
      <Num label="Étage min" value={f.floor_min} placeholder="Tous" onChange={(v) => up('floor_min', v)} />
      <label className="fld">Gare à pied
        <select value={f.station_max} onChange={(e) => up('station_max', e.target.value)}>
          <option value="">Peu importe</option><option value="10">≤ 10 min</option><option value="15">≤ 15 min</option><option value="20">≤ 20 min</option>
        </select></label>
      <div className="checks">
        <label><input type="checkbox" checked={f.fresh} onChange={(e) => up('fresh', e.target.checked)} /> 🆕 Nouveautés</label>
        <label><input type="checkbox" checked={f.gems} onChange={(e) => up('gems', e.target.checked)} /> 💎 Pépites</label>
        <label><input type="checkbox" checked={f.balcony} onChange={(e) => up('balcony', e.target.checked)} /> Balcon / terrasse</label>
        <label><input type="checkbox" checked={f.elevator} onChange={(e) => up('elevator', e.target.checked)} /> Ascenseur</label>
        <label><input type="checkbox" checked={f.favorites} onChange={(e) => up('favorites', e.target.checked)} /> ★ Mes favoris</label>
      </div>
      {sources.length > 1 && (
        <div className="chips">
          {sources.map((s) => (
            <button key={s} className={f.source.includes(s) ? 'chip on' : 'chip'}
              onClick={() => up('source', f.source.includes(s) ? f.source.filter((x) => x !== s) : [...f.source, s])}>{sourceLabel(s)}</button>
          ))}
        </div>
      )}
      <button className="link" onClick={reset}>Tout effacer</button>
    </section>
  )
}

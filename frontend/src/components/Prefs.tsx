import type { Filters, ScoreDefaults } from '../types'

interface Props { f: Filters; set: (f: Filters) => void; defaults: ScoreDefaults | null }

const LEVELS = ['Ignoré', 'Un peu', 'Moyen', 'Important', 'Très important', 'Essentiel']
const ROWS: { key: string; label: string; hint: string }[] = [
  { key: 'price', label: 'Prix bas', hint: 'Plus le prix est sous votre budget, mieux c\'est' },
  { key: 'surface', label: 'Grande surface', hint: 'Au moins la surface souhaitée' },
  { key: 'floor', label: 'Étage élevé', hint: 'Au moins l\'étage souhaité' },
  { key: 'view', label: 'Vue et lumière', hint: 'Vue dégagée, peu de vis-à-vis (si bâtiments connus)' },
  { key: 'station', label: 'Proche d\'une gare', hint: 'Distance à pied estimée' },
  { key: 'outdoor', label: 'Balcon ou terrasse', hint: 'Présence d\'un extérieur' },
  { key: 'deal', label: 'Bonne affaire', hint: 'Prix au m² sous les ventes réelles du secteur' },
]

export default function Prefs({ f, set, defaults }: Props) {
  const wk = (k: string) => `w_${k}` as keyof Filters
  const val = (k: string): number => {
    const v = f[wk(k)] as string
    return v !== '' ? Number(v) : (defaults?.weights[k] ?? 0)
  }
  const reset = () => set({ ...f, budget: '', surface_target: '', floor_target: '', w_price: '', w_surface: '', w_floor: '', w_view: '', w_station: '', w_outdoor: '', w_deal: '' })
  return (
    <details className="prefs">
      <summary>⭐ Mes préférences <small>- classe les annonces du meilleur au moins bon score</small></summary>
      <div className="prefgrid">
        {ROWS.map((r) => (
          <label key={r.key} className="pref" title={r.hint}>
            <span>{r.label} <b>{LEVELS[val(r.key)]}</b></span>
            <input type="range" min={0} max={5} value={val(r.key)} onChange={(e) => set({ ...f, [wk(r.key)]: e.target.value })} />
          </label>
        ))}
      </div>
      <div className="row targets">
        <label className="fld">Budget idéal (€)<input type="number" value={f.budget} placeholder={String(defaults?.budget ?? '')} onChange={(e) => set({ ...f, budget: e.target.value })} /></label>
        <label className="fld">Surface souhaitée (m²)<input type="number" value={f.surface_target} placeholder={String(defaults?.surface ?? '')} onChange={(e) => set({ ...f, surface_target: e.target.value })} /></label>
        <label className="fld">Étage souhaité (min)<input type="number" value={f.floor_target} placeholder={String(defaults?.floor ?? '')} onChange={(e) => set({ ...f, floor_target: e.target.value })} /></label>
        <button className="link" onClick={reset}>Remettre par défaut</button>
      </div>
      <p className="hint">Une information manquante ne pénalise pas une annonce (note neutre). Pour les enchères, le prix pris en compte est le prix final estimé, pas la mise à prix.</p>
    </details>
  )
}

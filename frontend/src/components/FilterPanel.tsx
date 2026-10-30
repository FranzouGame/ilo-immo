import { useState } from 'react'
import { api, download } from '../api'
import type { AppConfig, Criterion, CriterionOverride, Spec } from '../types'

interface Props {
  config: AppConfig
  spec: Spec
  setSpec: (s: Spec) => void
  tags: string[]
  total: number
}
interface Saved { id: number; name: string; spec: Spec; alert_min_score: number | null }

const STATUSES = [['a_voir', 'À voir'], ['favori', 'Favori'], ['visite', 'Visité'], ['ecarte', 'Écarté']]

const numOrNull = (v: string): number | null => (v === '' ? null : Number(v))

function Row({ c, o, set }: { c: Criterion; o: CriterionOverride; set: (o: CriterionOverride) => void }) {
  const [open, setOpen] = useState(false)
  const weight = o.weight ?? c.weight
  const ideal = o.ideal ?? c.ideal ?? [null, null]
  const acc = o.acceptable ?? c.acceptable ?? [null, null]
  const hard = o.hard ?? {}
  return (
    <div className={`crit ${weight > 0 ? 'on' : ''}`}>
      <div className="crit-head">
        <button className="link" onClick={() => setOpen(!open)} title="Détails">{open ? '▾' : '▸'} {c.label}</button>
        <span className="w">{weight}</span>
      </div>
      <input type="range" min={0} max={5} step={1} value={weight} onChange={(e) => set({ ...o, weight: Number(e.target.value) })} aria-label={`Importance ${c.label}`} />
      {open && (
        <div className="crit-detail">
          {c.kind === 'range' && (
            <>
              <label>Idéal <input type="number" value={ideal[0] ?? ''} onChange={(e) => set({ ...o, ideal: [numOrNull(e.target.value), ideal[1]] })} />
                – <input type="number" value={ideal[1] ?? ''} onChange={(e) => set({ ...o, ideal: [ideal[0], numOrNull(e.target.value)] })} /></label>
              <label>Acceptable <input type="number" value={acc[0] ?? ''} onChange={(e) => set({ ...o, acceptable: [numOrNull(e.target.value), acc[1]] })} />
                – <input type="number" value={acc[1] ?? ''} onChange={(e) => set({ ...o, acceptable: [acc[0], numOrNull(e.target.value)] })} /></label>
              <label className="hard">Indispensable : min <input type="number" value={hard.min ?? ''} onChange={(e) => set({ ...o, hard: { ...hard, min: numOrNull(e.target.value) ?? undefined } })} />
                max <input type="number" value={hard.max ?? ''} onChange={(e) => set({ ...o, hard: { ...hard, max: numOrNull(e.target.value) ?? undefined } })} /></label>
            </>
          )}
          {c.kind === 'bool' && (
            <label><input type="checkbox" checked={!!hard.require} onChange={(e) => set({ ...o, hard: e.target.checked ? { require: true } : null })} /> Indispensable</label>
          )}
          {c.kind === 'set' && (
            <label>Valeurs souhaitées (virgules)
              <input value={(o.prefer ?? c.prefer ?? []).join(',')} onChange={(e) => set({ ...o, prefer: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) })} /></label>
          )}
        </div>
      )}
    </div>
  )
}

export default function FilterPanel({ config, spec, setSpec, tags, total }: Props) {
  const [saved, setSaved] = useState<Saved[]>([])
  const [name, setName] = useState('')
  const [alert, setAlert] = useState('')
  const loadSaved = () => void api<Saved[]>('/filters').then(setSaved)
  const setCrit = (key: string, o: CriterionOverride) => setSpec({ ...spec, criteria: { ...spec.criteria, [key]: o } })
  const preset = (n: string) => {
    const p = config.presets.find((x) => x.name === n)
    if (!p) return
    const criteria: Spec['criteria'] = {}
    for (const c of config.criteria) criteria[c.key] = { weight: p.weights[c.key] ?? 0 }
    setSpec({ ...spec, criteria })
  }
  const toggle = (list: string[] | undefined, v: string): string[] => {
    const l = list ?? []
    return l.includes(v) ? l.filter((x) => x !== v) : [...l, v]
  }
  const save = async () => {
    if (!name) return
    await api('/filters', { name, spec, alert_min_score: alert ? Number(alert) : null })
    setName('')
    loadSaved()
  }
  return (
    <aside className="filters">
      <h2>Filtres <small>{total} biens</small></h2>
      <input placeholder="Recherche texte" value={spec.q ?? ''} onChange={(e) => setSpec({ ...spec, q: e.target.value })} />
      <div className="chips">
        {STATUSES.map(([v, l]) => (
          <button key={v} className={spec.status?.includes(v!) ? 'chip on' : 'chip'} onClick={() => setSpec({ ...spec, status: toggle(spec.status, v!) })}>{l}</button>
        ))}
        {['appartement', 'maison'].map((t) => (
          <button key={t} className={spec.types?.includes(t) ? 'chip on' : 'chip'} onClick={() => setSpec({ ...spec, types: toggle(spec.types, t) })}>{t}</button>
        ))}
      </div>
      {tags.length > 0 && (
        <div className="chips">
          {tags.map((t) => {
            const cur = spec.criteria.tags?.hard?.any ?? []
            return <button key={t} className={cur.includes(t) ? 'chip on' : 'chip'} onClick={() => {
              const any = toggle(cur, t)
              setCrit('tags', { ...spec.criteria.tags, hard: any.length ? { any } : null })
            }}>#{t}</button>
          })}
        </div>
      )}
      <label className="row"><input type="checkbox" checked={!!spec.widen} onChange={(e) => setSpec({ ...spec, widen: e.target.checked })} /> Élargir la recherche (quasi éligibles)</label>
      <div className="row">
        <select onChange={(e) => preset(e.target.value)} defaultValue="">
          <option value="" disabled>Préréglage…</option>
          {config.presets.map((p) => <option key={p.name}>{p.name}</option>)}
        </select>
        <button onClick={() => setSpec({ criteria: {}, sort: 'score', order: 'desc' })}>Réinitialiser</button>
      </div>
      <p className="hint">Importance 0-5 : 0 = ignoré. Rien n'est exclu sauf « indispensable ».</p>
      {config.criteria.map((c) => <Row key={c.key} c={c} o={spec.criteria[c.key] ?? {}} set={(o) => setCrit(c.key, o)} />)}
      <h3>Enregistrer ce filtre</h3>
      <div className="row"><input placeholder="Nom" value={name} onChange={(e) => setName(e.target.value)} />
        <input className="narrow" placeholder="Alerte ≥" value={alert} onChange={(e) => setAlert(e.target.value)} title="Score minimal pour une alerte" />
        <button onClick={() => void save()}>OK</button></div>
      <button className="link" onClick={loadSaved}>Mes filtres enregistrés</button>
      {saved.map((s) => (
        <div className="row" key={s.id}>
          <button className="link" onClick={() => setSpec(s.spec)}>{s.name}{s.alert_min_score ? ` 🔔${s.alert_min_score}` : ''}</button>
          <button className="link" onClick={() => void api(`/filters/${s.id}`, undefined, 'DELETE').then(loadSaved)}>✕</button>
        </div>
      ))}
      <button onClick={() => void download('/properties/export', spec, 'biens.csv')}>Exporter en CSV</button>
    </aside>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../api'

interface Commune { insee: string; commune: string; median_ppm2: number; p25: number; p75: number; n: number }
interface Point { year: string; median_ppm2: number; n: number }

export function MarketView() {
  const [type, setType] = useState('appartement')
  const [rows, setRows] = useState<Commune[]>([])
  const [sel, setSel] = useState<Commune | null>(null)
  const [series, setSeries] = useState<Point[]>([])
  useEffect(() => { void api<Commune[]>(`/market/communes?type=${type}`).then(setRows) }, [type])
  useEffect(() => { if (sel) void api<Point[]>(`/market/series?insee=${sel.insee}&type=${type}`).then(setSeries) }, [sel, type])
  const max = Math.max(1, ...rows.map((r) => r.p75))
  const smax = Math.max(1, ...series.map((s) => s.median_ppm2))
  return (
    <div className="page">
      <h2>Marché (DVF) <select value={type} onChange={(e) => setType(e.target.value)}><option>appartement</option><option>maison</option></select></h2>
      {rows.length === 0 && <p className="hint">Aucune statistique : lancer <code>make ingest SRC=dvf</code>.</p>}
      <div className="cols">
        <div>{rows.map((r) => (
          <div key={r.insee} className={`bar ${sel?.insee === r.insee ? 'on' : ''}`} onClick={() => setSel(r)} title={`${r.n} ventes · Q1 ${r.p25} · Q3 ${r.p75}`}>
            <span>{r.commune}</span><i style={{ width: `${(r.median_ppm2 / max) * 100}%` }} /><b>{r.median_ppm2} €/m²</b></div>
        ))}</div>
        {sel && series.length > 0 && (
          <div><h3>{sel.commune} - évolution</h3>
            <svg viewBox="0 0 300 120" className="chart" role="img" aria-label="Évolution du prix au m²">
              <polyline fill="none" stroke="#2563eb" strokeWidth="2" points={series.map((s, i) => `${20 + (i * 260) / Math.max(1, series.length - 1)},${110 - (s.median_ppm2 / smax) * 95}`).join(' ')} />
              {series.map((s, i) => <text key={s.year} x={20 + (i * 260) / Math.max(1, series.length - 1)} y={118} fontSize="9" textAnchor="middle">{s.year}</text>)}
            </svg>
            <ul>{series.map((s) => <li key={s.year}>{s.year} : {s.median_ppm2} €/m² ({s.n} ventes)</li>)}</ul></div>
        )}
      </div>
    </div>
  )
}

interface Conn { name: string; label: string; license: string; terms_url: string; update_frequency: string; warning: string; enabled: boolean;
  last_run: { status: string; n: number; at: string; message: string } | null }

export function SourcesView() {
  const [rows, setRows] = useState<Conn[]>([])
  const load = () => void api<Conn[]>('/connectors').then(setRows)
  useEffect(load, [])
  return (
    <div className="page"><h2>Sources de données</h2>
      <p className="hint">Données ouvertes uniquement. Les connecteurs « biens à vendre » sont des squelettes désactivés : vérifier les CGU avant tout usage.</p>
      <table><thead><tr><th>Source</th><th>Licence</th><th>Fréquence</th><th>État</th><th>Dernier import</th><th /></tr></thead><tbody>
        {rows.map((r) => <tr key={r.name}><td><a href={r.terms_url} target="_blank" rel="noreferrer">{r.label}</a>{r.warning && <div className="warn">{r.warning}</div>}</td>
          <td>{r.license}</td><td>{r.update_frequency}</td><td>{r.enabled ? 'activé' : 'désactivé'}</td>
          <td>{r.last_run ? `${r.last_run.status} · ${r.last_run.n} · ${r.last_run.at.slice(0, 16)} ${r.last_run.message}` : '-'}</td>
          <td><button onClick={() => void api(`/connectors/${r.name}/run`, {}).then(() => setTimeout(load, 1500))}>Lancer</button></td></tr>)}
      </tbody></table>
    </div>
  )
}

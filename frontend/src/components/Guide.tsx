import { useState } from 'react'
import { AUCTION_SOURCE, AUCTION_STATS, GUIDE, RESERVE_TABLE } from '../lib/guide'

export default function Guide({ focus }: { focus: string | null }) {
  const [open, setOpen] = useState<string>(focus ?? 'enchere')
  return (
    <div className="guide">
      <h2>Comprendre les ventes que les grands sites montrent peu</h2>
      <p className="muted">Chaque type de vente a ses règles, ses avantages et ses pièges. Ces fiches sont informatives : pour un achat, faites-vous conseiller par un notaire ou un avocat.</p>
      {GUIDE.map((g) => (
        <details key={g.id} open={open === g.id} onToggle={(e) => { if ((e.target as HTMLDetailsElement).open) setOpen(g.id) }}>
          <summary><span className="gi">{g.icon}</span> <b>{g.title}</b><small>{g.tagline}</small></summary>
          {g.blocks.map((b) => (
            <div key={b.h} className="gblock">
              <h4>{b.h}</h4>
              {b.p && <p>{b.p}</p>}
              {b.list && <ul>{b.list.map((x) => <li key={x}>{x}</li>)}</ul>}
            </div>
          ))}
          {g.id === 'enchere' && (
            <div className="gblock">
              <h4>Les chiffres réels (2022-2026)</h4>
              <table><thead><tr><th>Territoire</th><th>Prix payé / voisinage (médiane)</th><th>1er - 3e quartile</th><th>Mise à prix / voisinage</th></tr></thead><tbody>
                {AUCTION_STATS.map((s) => <tr key={s.place}><td>{s.place}</td><td><b>{s.paid} %</b></td><td>{s.q1} - {s.q3} %</td><td>{s.reserve} %</td></tr>)}
              </tbody></table>
              <p className="hint">Lecture : en Essonne, un logement saisi part en médiane à 51 % du prix au m² des ventes voisines (hors frais).</p>
              <table><thead><tr><th>Mise à prix</th><th>Prix final médian / mise à prix</th></tr></thead><tbody>
                {RESERVE_TABLE.map((r) => <tr key={r.tranche}><td>{r.tranche}</td><td>{r.multiple}</td></tr>)}
              </tbody></table>
              <p className="hint">Source : <a href={AUCTION_SOURCE.url} target="_blank" rel="noreferrer">{AUCTION_SOURCE.label}</a>, data.gouv.fr. Ordres de grandeur : chaque vente est différente.</p>
            </div>
          )}
        </details>
      ))}
    </div>
  )
}

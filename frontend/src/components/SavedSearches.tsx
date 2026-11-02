import { useState } from 'react'

const KEY = 'ilo_searches'
interface Saved { name: string; qs: string }
const read = (): Saved[] => {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? '[]') as Saved[]
  } catch {
    return []
  }
}
const write = (l: Saved[]): void => {
  try {
    localStorage.setItem(KEY, JSON.stringify(l))
  } catch {
    /* stockage indisponible */
  }
}

/** Recherches enregistrées dans le navigateur (chaque visiteur a les siennes). */
export default function SavedSearches({ current, load }: { current: string; load: (qs: string) => void }) {
  const [list, setList] = useState<Saved[]>(read)
  const [name, setName] = useState('')
  const save = () => {
    if (!name.trim()) return
    const next = [...list.filter((s) => s.name !== name.trim()), { name: name.trim(), qs: current }]
    write(next)
    setList(next)
    setName('')
  }
  return (
    <div className="saved row">
      <input placeholder="Nom de cette recherche" value={name} onChange={(e) => setName(e.target.value)} />
      <button onClick={save}>Enregistrer</button>
      {list.map((s) => (
        <span key={s.name} className="chip savedchip">
          <button className="link" onClick={() => load(s.qs)}>{s.name}</button>
          <button className="link" aria-label={`Supprimer ${s.name}`} onClick={() => { const n = list.filter((x) => x.name !== s.name); write(n); setList(n) }}>✕</button>
        </span>
      ))}
    </div>
  )
}

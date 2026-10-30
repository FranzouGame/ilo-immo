import { useCallback, useEffect, useRef, useState } from 'react'
import { api, hasToken, setToken } from './api'
import AddForm from './components/AddForm'
import FilterBar from './components/FilterBar'
import ListingCard from './components/ListingCard'
import ListingModal from './components/ListingModal'
import Login from './components/Login'
import MapView from './components/MapView'
import { emptyFilters, fromQuery, toQuery } from './lib/filters'
import type { Filters, Property } from './types'

export interface AppConfig { department_name: string; map: { center: [number, number]; zoom: number } }

export default function App() {
  const [authed, setAuthed] = useState(hasToken())
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [f, setF] = useState<Filters>(() => fromQuery(window.location.hash))
  const [items, setItems] = useState<Property[]>([])
  const [total, setTotal] = useState(0)
  const [sources, setSources] = useState<string[]>([])
  const [openId, setOpenId] = useState<number | null>(null)
  const [adding, setAdding] = useState(false)
  const [view, setView] = useState<'liste' | 'carte'>('liste')
  const [error, setError] = useState('')
  const timer = useRef<number>()

  useEffect(() => {
    const out = () => setAuthed(false)
    window.addEventListener('ilo-logout', out)
    return () => window.removeEventListener('ilo-logout', out)
  }, [])
  useEffect(() => {
    if (authed) void api<AppConfig>('/config').then(setConfig).catch((e: Error) => setError(e.message))
  }, [authed])

  const load = useCallback(() => {
    const qs = toQuery(f)
    window.history.replaceState(null, '', qs ? `#${qs}` : window.location.pathname)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => {
      api<{ items: Property[]; total: number; sources: string[] }>(`/listings?${qs}`)
        .then((r) => { setItems(r.items); setTotal(r.total); setSources(r.sources); setError('') })
        .catch((e: Error) => setError(e.message))
    }, 250)
  }, [f])
  useEffect(() => { if (authed && config) load() }, [authed, config, load])

  if (!authed) return <Login onDone={() => setAuthed(true)} />
  if (!config) return <p className="center">{error || 'Chargement…'}</p>
  const open = items.find((p) => p.id === openId) ?? null
  const fav = (p: Property) => void api(`/properties/${p.id}`, { status: p.status === 'favori' ? 'a_voir' : 'favori' }, 'PATCH').then(load)
  return (
    <div className="site">
      <header>
        <b className="logo">Ilo</b><span className="muted">Annonces hors grands sites · {config.department_name}</span>
        <button className="primary" onClick={() => setAdding(true)}>+ Ajouter une annonce</button>
        <button className="link" onClick={() => { setToken(''); setAuthed(false) }}>Quitter</button>
      </header>
      <FilterBar f={f} set={setF} sources={sources} reset={() => setF(emptyFilters())} />
      <div className="toolbar">
        <b>{total} annonce{total > 1 ? 's' : ''}</b>
        <select value={f.sort} onChange={(e) => setF({ ...f, sort: e.target.value })} aria-label="Trier">
          <option value="recent">Plus récentes</option><option value="price_asc">Prix croissant</option><option value="price_desc">Prix décroissant</option>
          <option value="ppm2">Prix au m²</option><option value="surface">Plus grandes</option>
        </select>
        <div className="seg">
          <button className={view === 'liste' ? 'on' : ''} onClick={() => setView('liste')}>Liste</button>
          <button className={view === 'carte' ? 'on' : ''} onClick={() => setView('carte')}>Carte</button>
        </div>
      </div>
      {error && <p className="err">{error}</p>}
      {view === 'liste' ? (
        <main className="grid-list">
          {items.map((p) => <ListingCard key={p.id} p={p} onOpen={() => setOpenId(p.id)} onFav={() => fav(p)} />)}
          {items.length === 0 && <p className="empty">Aucune annonce pour ces critères. Élargissez la recherche ou lancez <code>make ingest</code>.</p>}
        </main>
      ) : <main className="mapmain"><MapView config={config} items={items} onOpen={setOpenId} /></main>}
      {open && <ListingModal p={open} onClose={() => setOpenId(null)} onChanged={load} />}
      {adding && <AddForm onClose={() => setAdding(false)} onCreated={() => { setAdding(false); load() }} />}
    </div>
  )
}

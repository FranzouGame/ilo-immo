import { useCallback, useEffect, useRef, useState } from 'react'
import { api, hasToken, setToken } from './api'
import FilterPanel from './components/FilterPanel'
import Login from './components/Login'
import MapView from './components/MapView'
import { MarketView, SourcesView } from './components/Pages'
import PropertyDetail from './components/PropertyDetail'
import PropertyForm from './components/PropertyForm'
import PropertyList from './components/PropertyList'
import { specFromHash, specToHash } from './lib/urlState'
import type { AppConfig, Property, Spec } from './types'

export default function App() {
  const [authed, setAuthed] = useState(hasToken())
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [spec, setSpec] = useState<Spec>(() => specFromHash(window.location.hash))
  const [items, setItems] = useState<Property[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [selId, setSelId] = useState<number | null>(null)
  const [detail, setDetail] = useState<Property | null>(null)
  const [mode3d, setMode3d] = useState(false)
  const [direction, setDirection] = useState('S')
  const [tab, setTab] = useState<'biens' | 'marche' | 'sources'>('biens')
  const [adding, setAdding] = useState(false)
  const [showFilters, setShowFilters] = useState(true)
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

  const refresh = useCallback(() => {
    window.history.replaceState(null, '', specToHash(spec))
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => {
      api<{ items: Property[] }>('/properties/search', spec).then((r) => { setItems(r.items); setError('') }).catch((e: Error) => setError(e.message))
      void api<string[]>('/tags').then(setTags)
    }, 250)
  }, [spec])
  useEffect(() => { if (authed && config) refresh() }, [authed, config, refresh])

  if (!authed) return <Login onDone={() => setAuthed(true)} />
  if (!config) return <p className="center">{error || 'Chargement…'}</p>
  const scored = items.find((p) => p.id === selId)
  const selected = detail && detail.id === selId ? { ...detail, score: scored?.score } : (scored ?? null)
  return (
    <div className="app">
      <header>
        <b>Ilo</b> <span className="muted">{config.department_name} ({config.department})</span>
        <nav>
          {(['biens', 'marche', 'sources'] as const).map((t) => <button key={t} className={tab === t ? 'on' : ''} onClick={() => setTab(t)}>{t === 'biens' ? 'Biens' : t === 'marche' ? 'Marché' : 'Sources'}</button>)}
        </nav>
        <button className="show-filters" onClick={() => setShowFilters(!showFilters)}>Filtres</button>
        <button className="primary" onClick={() => setAdding(true)}>+ Ajouter</button>
        <button onClick={() => { setToken(''); setAuthed(false) }}>Quitter</button>
      </header>
      {error && <p className="err">{error}</p>}
      {tab === 'marche' && <MarketView />}
      {tab === 'sources' && <SourcesView />}
      {tab === 'biens' && (
        <main>
          {showFilters && <FilterPanel config={config} spec={spec} setSpec={setSpec} tags={tags} total={items.length} />}
          <PropertyList items={items} selected={selId} onSelect={(id) => { setSelId(id); setMode3d(false) }} sort={spec.sort ?? 'score'} setSort={(s) => setSpec({ ...spec, sort: s, order: s === 'price' || s === 'price_m2' ? 'asc' : 'desc' })} />
          <div className="mapwrap">
            <MapView config={config} items={items} selected={selected} onSelect={setSelId} mode3d={mode3d} direction={direction} />
          </div>
          {selId != null && <PropertyDetail id={selId} score={scored} onClose={() => { setSelId(null); setMode3d(false) }} onChanged={refresh} onLoaded={setDetail}
            mode3d={mode3d} setMode3d={setMode3d} direction={direction} setDirection={setDirection} />}
        </main>
      )}
      {adding && <PropertyForm onClose={() => setAdding(false)} onCreated={(id) => { setAdding(false); setSelId(id); refresh() }} />}
    </div>
  )
}

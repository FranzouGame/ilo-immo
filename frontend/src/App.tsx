import { useCallback, useEffect, useRef, useState } from 'react'
import { api, hasToken, setToken } from './api'
import AddForm from './components/AddForm'
import Compare from './components/Compare'
import FilterBar from './components/FilterBar'
import Guide from './components/Guide'
import ListingCard from './components/ListingCard'
import ListingModal from './components/ListingModal'
import Login from './components/Login'
import MapView from './components/MapView'
import Prefs from './components/Prefs'
import SavedSearches from './components/SavedSearches'
import { downloadCsv } from './lib/csv'
import { emptyFilters, fromQuery, toQuery } from './lib/filters'
import { loadFinance, saveFinance, type Fees, type Finance } from './lib/finance'
import { isGem, isNew } from './lib/kinds'
import { previousVisit } from './lib/visit'
import { STATIC, listings, loadData, setStatusLocal } from './lib/staticApi'
import type { Filters, Property, ScoreDefaults } from './types'

export interface AppConfig {
  department_name: string
  departments: { code: string; name: string }[]
  map: { center: [number, number]; zoom: number }
  finance: Finance
  fees_pct: Fees
}

export default function App() {
  const [authed, setAuthed] = useState(STATIC || hasToken())
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [f, setF] = useState<Filters>(() => fromQuery(window.location.hash))
  const [items, setItems] = useState<Property[]>([])
  const [total, setTotal] = useState(0)
  const [sources, setSources] = useState<string[]>([])
  const [openId, setOpenId] = useState<number | null>(null)
  const [adding, setAdding] = useState(false)
  const [view, setView] = useState<'liste' | 'carte'>('liste')
  const [page, setPage] = useState<'annonces' | 'guide'>('annonces')
  const [guideFocus, setGuideFocus] = useState<string | null>(null)
  const [defaults, setDefaults] = useState<ScoreDefaults | null>(null)
  const [error, setError] = useState('')
  const [updated, setUpdated] = useState('')
  const [filtersOpen, setFiltersOpen] = useState(() => window.innerWidth > 700)
  const [fin, setFin] = useState<Finance | null>(null)
  const [cmp, setCmp] = useState<number[]>([])
  const [comparing, setComparing] = useState(false)
  const lastVisit = useRef<number | null>(previousVisit())
  const timer = useRef<number>()

  useEffect(() => {
    const out = () => setAuthed(false)
    window.addEventListener('ilo-logout', out)
    return () => window.removeEventListener('ilo-logout', out)
  }, [])
  useEffect(() => {
    if (!authed) return
    const cfg = STATIC ? loadData().then((d) => { setUpdated(d.generated_at); return d.config as AppConfig }) : api<AppConfig>('/config')
    void cfg.then((c) => { setConfig(c); setFin(loadFinance(c.finance)) }).catch((e: Error) => setError(e.message))
  }, [authed])

  const load = useCallback(() => {
    const qs = toQuery(f)
    window.history.replaceState(null, '', qs ? `#${qs}` : window.location.pathname)
    window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => {
      const res = STATIC ? loadData().then((d) => listings(d, f)) : api<{ items: Property[]; total: number; sources: string[]; defaults: ScoreDefaults }>(`/listings?${qs}`)
      res.then((r) => { setItems(r.items); setTotal(r.total); setSources(r.sources); setDefaults(r.defaults); setError('') })
        .catch((e: Error) => setError(e.message))
    }, 250)
  }, [f])
  useEffect(() => { if (authed && config) load() }, [authed, config, load])

  if (!authed) return <Login onDone={() => setAuthed(true)} />
  if (!config || !fin) return <p className="center">{error || 'Chargement…'}</p>
  const shown = items.filter((p) => (!f.fresh || isNew(p, lastVisit.current)) && (!f.gems || isGem(p)))
  const open = items.find((p) => p.id === openId) ?? null
  const fees = config.fees_pct
  const setStatus = (p: Property, status: string) => {
    if (STATIC) { setStatusLocal(p.id, status); load() } else void api(`/properties/${p.id}`, { status }, 'PATCH').then(load)
  }
  const fav = (p: Property) => setStatus(p, p.status === 'favori' ? 'a_voir' : 'favori')
  return (
    <div className="site">
      <header>
        <b className="logo">Ilo</b><span className="muted">Annonces hors grands sites · {config.department_name}</span>
        <nav className="tabs">
          <button className={page === 'annonces' ? 'on' : ''} onClick={() => setPage('annonces')}>Annonces</button>
          <button className={page === 'guide' ? 'on' : ''} onClick={() => { setGuideFocus(null); setPage('guide') }}>Comprendre les ventes</button>
        </nav>
        {!STATIC && <button className="primary" onClick={() => setAdding(true)}>+ Ajouter une annonce</button>}
        {!STATIC && <button className="link" onClick={() => { setToken(''); setAuthed(false) }}>Quitter</button>}
      </header>
      {page === 'guide' ? <Guide focus={guideFocus} /> : (<>
      {filtersOpen && <FilterBar departments={config.departments} f={f} set={setF} sources={sources} reset={() => setF(emptyFilters())} />}
      <Prefs f={f} set={setF} defaults={defaults} fin={fin} setFin={(x) => { setFin(x); saveFinance(x) }} />
      {filtersOpen && <SavedSearches current={toQuery(f)} load={(qs) => setF(fromQuery(qs))} />}
      <div className="toolbar">
        <b>{shown.length} annonce{shown.length > 1 ? 's' : ''}{shown.length !== total ? ` (sur ${total})` : ''}</b>
        <button onClick={() => setFiltersOpen(!filtersOpen)}>{filtersOpen ? 'Masquer les filtres' : 'Filtres'}</button>
        <select value={f.sort} onChange={(e) => setF({ ...f, sort: e.target.value })} aria-label="Trier">
          <option value="score">Meilleur score</option><option value="recent">Plus récentes</option><option value="price_asc">Prix croissant</option><option value="price_desc">Prix décroissant</option>
          <option value="deal">Meilleures affaires</option><option value="ppm2">Prix au m²</option><option value="surface">Plus grandes</option>
        </select>
        <button onClick={() => downloadCsv(shown)} title="Télécharger les annonces affichées (Excel)">⬇ CSV</button>
        <div className="seg">
          <button className={view === 'liste' ? 'on' : ''} onClick={() => setView('liste')}>Liste</button>
          <button className={view === 'carte' ? 'on' : ''} onClick={() => setView('carte')}>Carte</button>
        </div>
      </div>
      {error && <p className="err">{error}</p>}
      {view === 'liste' ? (
        <main className="grid-list">
          {shown.map((p) => (
            <ListingCard key={p.id} p={p} lastVisit={lastVisit.current} fin={fin} fees={fees} compared={cmp.includes(p.id)} onOpen={() => setOpenId(p.id)} onFav={() => fav(p)}
              onCompare={() => setCmp((c) => (c.includes(p.id) ? c.filter((x) => x !== p.id) : [...c, p.id].slice(-3)))} />
          ))}
          {shown.length === 0 && <p className="empty">Aucune annonce pour ces critères. Élargissez la recherche ou lancez <code>make ingest</code>.</p>}
        </main>
      ) : <main className="mapmain"><MapView config={config} items={shown} onOpen={setOpenId} /></main>}
      </>)}
      {cmp.length > 0 && (
        <div className="cmpbar">
          <b>{cmp.length}/3 à comparer</b>
          <button className="primary" disabled={cmp.length < 2} onClick={() => setComparing(true)}>Comparer</button>
          <button className="link" onClick={() => setCmp([])}>Vider</button>
        </div>
      )}
      {comparing && <Compare items={items.filter((p) => cmp.includes(p.id))} fin={fin} fees={fees} onClose={() => setComparing(false)} />}
      {open && <ListingModal p={open} fin={fin} fees={fees} canDelete={!STATIC} setStatus={(s) => setStatus(open, s)} onClose={() => setOpenId(null)} onChanged={load} openGuide={(id) => { setOpenId(null); setGuideFocus(id); setPage('guide') }} />}
      {adding && <AddForm onClose={() => setAdding(false)} onCreated={() => { setAdding(false); load() }} />}
      {STATIC && (
        <footer className="foot">
          Mis à jour le {updated.slice(0, 10)} · Annonces issues de licitor.com, 36h-immo.com, immonot.com, proprietairemaintenant.fr et costes-viager.com (liens vers les annonces d'origine) · <a href={`${import.meta.env.BASE_URL}feed.xml`}>Flux RSS des nouveautés</a> ·
          Prix du marché : DVF (Etalab) · Cartes : OpenFreeMap, © OpenStreetMap · Estimations indicatives, sans valeur de conseil.
          Favoris et masquages sont enregistrés dans votre navigateur.
        </footer>
      )}
    </div>
  )
}

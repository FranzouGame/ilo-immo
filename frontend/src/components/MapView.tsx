import maplibregl from 'maplibre-gl'
import { useEffect, useRef } from 'react'
import type { AppConfig } from '../App'
import { scoreColor } from '../lib/format'
import type { Property } from '../types'

const STYLE = (import.meta.env.VITE_MAP_STYLE_URL as string | undefined) || 'https://tiles.openfreemap.org/styles/liberty'

export default function MapView({ config, items, onOpen }: { config: AppConfig; items: Property[]; onOpen: (id: number) => void }) {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const markers = useRef<maplibregl.Marker[]>([])
  const open = useRef(onOpen)
  open.current = onOpen

  useEffect(() => {
    if (!el.current) return
    const m = new maplibregl.Map({ container: el.current, style: STYLE, center: config.map.center, zoom: config.map.zoom })
    m.addControl(new maplibregl.NavigationControl())
    map.current = m
    return () => m.remove()
  }, [config])

  useEffect(() => {
    const m = map.current
    if (!m) return
    markers.current.forEach((k) => k.remove())
    const pts = items.filter((p) => p.lon != null && p.lat != null)
    const groups = new Map<string, number>()
    const spread = (p: Property): [number, number] => {  // annonces au même point (centre de commune) : on les écarte en spirale
      const key = `${(p.lon as number).toFixed(4)},${(p.lat as number).toFixed(4)}`
      const k = groups.get(key) ?? 0
      groups.set(key, k + 1)
      const r = k === 0 ? 0 : 0.0013 * Math.sqrt(k)
      return [(p.lon as number) + (r * Math.cos(k * 2.4)) * 1.5, (p.lat as number) + r * Math.sin(k * 2.4)]
    }
    markers.current = pts.map((p) => {
      const d = document.createElement('button')
      d.className = 'pin'
      d.textContent = p.price ? `${Math.round(p.price / 1000)} k€` : '?'
      d.style.background = scoreColor(p.score)
      d.title = `Score ${p.score}`
      d.onclick = () => open.current(p.id)
      return new maplibregl.Marker({ element: d }).setLngLat(spread(p)).addTo(m)
    })
    if (pts.length) {
      const b = new maplibregl.LngLatBounds()
      pts.forEach((p) => b.extend([p.lon as number, p.lat as number]))
      m.fitBounds(b, { padding: 60, maxZoom: 14, duration: 0 })
    }
  }, [items])

  return <div className="map" ref={el} />
}

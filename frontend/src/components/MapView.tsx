import maplibregl from 'maplibre-gl'
import { useEffect, useRef } from 'react'
import type { AppConfig } from '../App'
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
    markers.current = pts.map((p) => {
      const d = document.createElement('button')
      d.className = 'pin'
      d.textContent = p.price ? `${Math.round(p.price / 1000)} k€` : '?'
      d.onclick = () => open.current(p.id)
      return new maplibregl.Marker({ element: d }).setLngLat([p.lon as number, p.lat as number]).addTo(m)
    })
    if (pts.length) {
      const b = new maplibregl.LngLatBounds()
      pts.forEach((p) => b.extend([p.lon as number, p.lat as number]))
      m.fitBounds(b, { padding: 60, maxZoom: 14, duration: 0 })
    }
  }, [items])

  return <div className="map" ref={el} />
}

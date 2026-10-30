import maplibregl from 'maplibre-gl'
import { useEffect, useRef } from 'react'
import { api } from '../api'
import { cone, dirBearing } from '../lib/geo'
import type { AppConfig, Property } from '../types'

const STYLE = (import.meta.env.VITE_MAP_STYLE_URL as string | undefined) || 'https://tiles.openfreemap.org/styles/liberty'

interface Props {
  config: AppConfig
  items: Property[]
  selected: Property | null
  onSelect: (id: number) => void
  mode3d: boolean
  direction: string
}

const emptyFc = { type: 'FeatureCollection', features: [] } as GeoJSON.FeatureCollection

export default function MapView({ config, items, selected, onSelect, mode3d, direction }: Props) {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const ready = useRef(false)
  const onSelectRef = useRef(onSelect)
  onSelectRef.current = onSelect

  useEffect(() => {
    if (!el.current) return
    const m = new maplibregl.Map({ container: el.current, style: STYLE, center: config.map.center, zoom: config.map.zoom })
    map.current = m
    m.addControl(new maplibregl.NavigationControl())
    m.on('load', () => {
      m.addSource('props', { type: 'geojson', data: emptyFc })
      m.addSource('bd', { type: 'geojson', data: emptyFc })
      m.addSource('cone', { type: 'geojson', data: emptyFc })
      m.addLayer({ id: 'bd-3d', type: 'fill-extrusion', source: 'bd', paint: { 'fill-extrusion-color': '#9aa5b1', 'fill-extrusion-height': ['get', 'height'], 'fill-extrusion-opacity': 0.8 } })
      m.addLayer({ id: 'cone', type: 'fill', source: 'cone', paint: { 'fill-color': '#ff8a00', 'fill-opacity': 0.35 } })
      m.addLayer({ id: 'props', type: 'circle', source: 'props', paint: {
        'circle-radius': ['case', ['==', ['get', 'sel'], 1], 11, 7], 'circle-stroke-width': 2, 'circle-stroke-color': '#fff',
        'circle-color': ['step', ['coalesce', ['get', 'score'], -1], '#888', 0, '#c0392b', 35, '#e06b00', 55, '#e0a100', 75, '#1b9e5a'] } })
      m.on('click', 'props', (e) => {
        const id = e.features?.[0]?.properties?.id as number | undefined
        if (id != null) onSelectRef.current(id)
      })
      m.on('mouseenter', 'props', () => (m.getCanvas().style.cursor = 'pointer'))
      m.on('mouseleave', 'props', () => (m.getCanvas().style.cursor = ''))
      ready.current = true
      m.fire('ilo-ready')
    })
    return () => m.remove()
  }, [config])

  const src = (name: string, data: GeoJSON.FeatureCollection) => (map.current?.getSource(name) as maplibregl.GeoJSONSource | undefined)?.setData(data)

  useEffect(() => {
    const draw = () => src('props', { type: 'FeatureCollection', features: items.filter((p) => p.lon != null && p.lat != null).map((p) => ({
      type: 'Feature', geometry: { type: 'Point', coordinates: [p.lon as number, p.lat as number] },
      properties: { id: p.id, score: p.score ?? -1, sel: p.id === selected?.id ? 1 : 0 } })) })
    if (ready.current) draw()
    else map.current?.once('ilo-ready', draw)
  }, [items, selected?.id])

  useEffect(() => {
    const m = map.current
    if (!m || !selected || selected.lon == null || selected.lat == null) return
    const { lon, lat } = selected as { lon: number; lat: number }
    const run = () => {
      if (mode3d) {
        void api<GeoJSON.FeatureCollection>(`/buildings?lon=${lon}&lat=${lat}&radius=350`).then((fc) => src('bd', fc))
        const bearing = dirBearing(direction)
        src('cone', { type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [cone(lon, lat, bearing)] } }] })
        m.easeTo({ center: [lon, lat], zoom: 17.5, pitch: 65, bearing })
      } else {
        src('bd', emptyFc)
        src('cone', emptyFc)
        m.easeTo({ center: [lon, lat], zoom: Math.max(m.getZoom(), 13), pitch: 0, bearing: 0 })
      }
    }
    if (ready.current) run()
    else m.once('ilo-ready', run)
  }, [selected?.id, selected?.lon, selected?.lat, mode3d, direction]) // eslint-disable-line react-hooks/exhaustive-deps

  return <div className="map" ref={el} />
}

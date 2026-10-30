export interface Criterion {
  key: string
  label: string
  kind: 'range' | 'bool' | 'set'
  field: string
  ideal?: [number | null, number | null]
  acceptable?: [number | null, number | null]
  prefer?: string[]
  weight: number
  manual?: string
}
export interface Hard {
  min?: number
  max?: number
  require?: boolean
  any?: string[]
}
export interface CriterionOverride {
  weight?: number
  ideal?: [number | null, number | null]
  acceptable?: [number | null, number | null]
  prefer?: string[]
  hard?: Hard | null
}
export interface Spec {
  criteria: Record<string, CriterionOverride>
  q?: string
  status?: string[]
  types?: string[]
  widen?: boolean
  sort?: string
  order?: 'asc' | 'desc'
}
export interface AppConfig {
  department: string
  department_name: string
  map: { center: [number, number]; zoom: number }
  criteria: Criterion[]
  presets: { name: string; weights: Record<string, number> }[]
  view: Record<string, number>
}
export interface Sector {
  distance_m: number
  open: boolean
  floors_above: number
  height_diff_m: number
}
export interface Computed {
  sectors?: Record<string, Sector>
  sky_index?: number
  best_clearance_m?: number
  window_altitude_m?: number
  ground_altitude_m?: number
  relative_floor?: number
  vis_a_vis?: { score: number; sector: string; explanation: string }
  view_quality?: { score: number; reasons: string[] }
  noise_score?: number
  station_walk_m?: number
  parks_count?: number
  market_gap_pct?: number
  market_ppm2?: number
  market_ref?: { scope: string; median_ppm2: number; n: number }
  georisks?: { count: number; items: string[] }
  has_buildings?: boolean
}
export interface Property {
  id: number
  title: string
  url: string | null
  type: string
  price: number | null
  surface: number | null
  rooms: number | null
  floor: number | null
  floors_total: number | null
  balcony: boolean | null
  elevator: boolean | null
  orientation: string | null
  year_built: number | null
  address: string | null
  commune: string | null
  dpe: string | null
  ges: string | null
  condition: string | null
  status: string
  notes: string
  tags: string[]
  manual_view: number | null
  manual_light: number | null
  manual_vis_a_vis: number | null
  photos: string[]
  lon: number | null
  lat: number | null
  price_m2: number | null
  computed: Computed
  score?: number
  near?: boolean
  breakdown?: { key: string; label: string; value: unknown; score: number | null; manual: boolean; weight: number }[]
  neighbor_sales?: { sold_on: string; price: number; surface: number; price_m2: number; address: string | null; dist: number }[]
}

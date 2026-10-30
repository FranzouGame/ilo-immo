export interface Computed {
  vis_a_vis?: { score: number; explanation: string }
  view_quality?: { score: number; reasons: string[] }
  window_altitude_m?: number
  station_walk_m?: number
  market_gap_pct?: number
  market_ref?: { median_ppm2: number; scope: string; n: number }
  georisks?: { count: number; items: string[] }
  has_buildings?: boolean
}
export interface Property {
  id: number
  source: string
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
  postcode: string | null
  dpe: string | null
  status: string
  notes: string
  tags: string[]
  photos: string[]
  lon: number | null
  lat: number | null
  price_m2: number | null
  created_at: string
  computed: Computed
}
export interface Filters {
  q: string
  type: string
  price_max: string
  surface_min: string
  rooms_min: string
  floor_min: string
  balcony: boolean
  elevator: boolean
  favorites: boolean
  source: string[]
  sort: string
}

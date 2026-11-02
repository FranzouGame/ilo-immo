export interface AuctionInfo {
  paid_pct: { median: number; q1: number; q3: number }
  occupied: boolean
  market_value?: number
  reserve_pct_of_value?: number
  deal_pct?: number
  reserve: number
  deposit: number
  multiple: number
  surenchere_pct: number
  estimate: number
  by_multiple: number
  by_market?: { q1: number; median: number; q3: number }
  ratios: { median: number; q1: number; q3: number }
}
export interface Computed {
  auction?: AuctionInfo
  deal_pct?: number
  score_price?: number
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
  kind: 'enchere' | 'interactive' | 'viager' | 'aide' | 'notaire' | 'autre'
  price_history: { date: string; price: number }[]
  custom: Record<string, unknown>
  score: number
  breakdown: { key: string; label: string; value: unknown; score: number | null; manual: boolean; weight: number }[]
  computed: Computed
}
export interface Filters {
  q: string
  dept: string
  type: string
  price_max: string
  surface_min: string
  rooms_min: string
  floor_min: string
  station_max: string
  fresh: boolean
  gems: boolean
  balcony: boolean
  elevator: boolean
  favorites: boolean
  source: string[]
  sort: string
  // Mes préférences (vide = valeur par défaut du serveur)
  budget: string
  surface_target: string
  floor_target: string
  w_price: string
  w_surface: string
  w_floor: string
  w_view: string
  w_station: string
  w_outdoor: string
  w_deal: string
}
export interface ScoreDefaults {
  weights: Record<string, number>
  budget: number
  surface: number
  floor: number
}

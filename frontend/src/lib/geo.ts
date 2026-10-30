const DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
export const dirBearing = (d: string): number => Math.max(0, DIRS.indexOf(d)) * 45
export const DIRECTIONS = DIRS

/** Cône de vue (polygone GeoJSON) : sommet au bien, ouverture `spread`° de part et d'autre du cap. */
export function cone(lon: number, lat: number, bearing: number, spread = 30, radiusM = 300): [number, number][] {
  const kx = 111_320 * Math.cos((lat * Math.PI) / 180)
  const ring: [number, number][] = [[lon, lat]]
  for (let a = bearing - spread; a <= bearing + spread; a += spread / 6) {
    const r = (a * Math.PI) / 180
    ring.push([lon + (radiusM * Math.sin(r)) / kx, lat + (radiusM * Math.cos(r)) / 110_540])
  }
  ring.push([lon, lat])
  return ring
}

export const streetViewUrl = (lat: number, lon: number): string =>
  `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lon}`
export const mapillaryUrl = (lat: number, lon: number): string => `https://www.mapillary.com/app/?lat=${lat}&lng=${lon}&z=18`
export const earthUrl = (lat: number, lon: number): string => `https://earth.google.com/web/@${lat},${lon},100a,300d,35y,0h,60t,0r`

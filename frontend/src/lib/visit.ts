const PREV = 'ilo_visit_prev'
const CUR = 'ilo_visit_cur'
const SESSION_MS = 30 * 60_000

/** Date de la visite précédente (pour « nouveau depuis ma dernière visite »). Un rechargement dans la demi-heure ne compte pas comme une nouvelle visite. */
export function previousVisit(now = Date.now()): number | null {
  try {
    const cur = Number(localStorage.getItem(CUR))
    if (cur && now - cur > SESSION_MS) localStorage.setItem(PREV, String(cur))
    localStorage.setItem(CUR, String(now))
    return Number(localStorage.getItem(PREV)) || null
  } catch {
    return null
  }
}

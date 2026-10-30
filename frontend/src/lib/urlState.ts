import type { Spec } from '../types'

export const emptySpec = (): Spec => ({ criteria: {}, sort: 'score', order: 'desc' })

export function encodeSpec(spec: Spec): string {
  return btoa(unescape(encodeURIComponent(JSON.stringify(spec))))
}

export function decodeSpec(s: string): Spec {
  try {
    const v = JSON.parse(decodeURIComponent(escape(atob(s)))) as Spec
    return { ...emptySpec(), ...v }
  } catch {
    return emptySpec()
  }
}

export const specFromHash = (hash: string): Spec => {
  const m = /f=([^&]+)/.exec(hash)
  try {
    return m && m[1] ? decodeSpec(decodeURIComponent(m[1])) : emptySpec()
  } catch {
    return emptySpec()
  }
}
export const specToHash = (spec: Spec): string => `#f=${encodeURIComponent(encodeSpec(spec))}`

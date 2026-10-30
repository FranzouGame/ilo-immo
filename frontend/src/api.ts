const KEY = 'ilo_token'
const get = (): string => {
  try {
    return localStorage.getItem(KEY) ?? ''
  } catch {
    return ''
  }
}
export const setToken = (t: string): void => {
  try {
    if (t) localStorage.setItem(KEY, t)
    else localStorage.removeItem(KEY)
  } catch {
    /* stockage indisponible : session non persistée */
  }
}
export const hasToken = (): boolean => get() !== ''

export async function api<T>(path: string, body?: unknown, method?: string): Promise<T> {
  const r = await fetch(`/api${path}`, {
    method: method ?? (body === undefined ? 'GET' : 'POST'),
    headers: { 'content-type': 'application/json', authorization: `Bearer ${get()}` },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (r.status === 401) {
    setToken('')
    window.dispatchEvent(new Event('ilo-logout'))
  }
  if (!r.ok) throw new Error(((await r.json().catch(() => ({}))) as { detail?: string }).detail ?? `Erreur ${r.status}`)
  return r.status === 204 ? (undefined as T) : ((await r.json()) as T)
}

export async function download(path: string, body: unknown, filename: string): Promise<void> {
  const r = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${get()}` },
    body: JSON.stringify(body),
  })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(await r.blob())
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

export async function upload<T>(path: string, file: File): Promise<T> {
  const fd = new FormData()
  fd.append('file', file)
  const r = await fetch(`/api${path}`, { method: 'POST', headers: { authorization: `Bearer ${get()}` }, body: fd })
  if (!r.ok) throw new Error(`Erreur ${r.status}`)
  return (await r.json()) as T
}

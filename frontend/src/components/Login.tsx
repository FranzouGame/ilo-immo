import { useState } from 'react'
import { api, setToken } from '../api'

export default function Login({ onDone }: { onDone: () => void }) {
  const [pw, setPw] = useState('')
  const [err, setErr] = useState('')
  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const r = await api<{ token: string }>('/auth/login', { password: pw })
      setToken(r.token)
      onDone()
    } catch (x) {
      setErr((x as Error).message)
    }
  }
  return (
    <form className="login" onSubmit={(e) => void submit(e)}>
      <h1>Ilo</h1>
      <p>Recherche immobilière - Essonne</p>
      <input type="password" placeholder="Mot de passe" value={pw} onChange={(e) => setPw(e.target.value)} autoFocus />
      <button className="primary">Entrer</button>
      {err && <p className="err">{err}</p>}
    </form>
  )
}

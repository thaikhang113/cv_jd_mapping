import { createContext, useContext, useEffect, useState } from 'react'
import api from '../api/axiosClient'

const AuthContext = createContext(null)
export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('user') || 'null'))
  const [loading, setLoading] = useState(false)
  const save = (data) => { localStorage.setItem('token', data.access_token); localStorage.setItem('user', JSON.stringify(data.user)); setUser(data.user) }
  const login = async (email, password) => save((await api.post('/api/auth/login', { email, password })).data)
  const register = async (payload) => save((await api.post('/api/auth/register', payload)).data)
  const logout = () => { localStorage.clear(); setUser(null) }
  useEffect(() => { if (localStorage.getItem('token')) api.get('/api/auth/me').then(r => { setUser(r.data); localStorage.setItem('user', JSON.stringify(r.data)) }).catch(logout).finally(() => setLoading(false)) }, [])
  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>
}
export const useAuth = () => useContext(AuthContext)

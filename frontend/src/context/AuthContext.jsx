import { createContext, useContext, useEffect, useState } from 'react'
import api, { clearStoredAuth, getStoredToken } from '../api/axiosClient'

const AuthContext = createContext(null)
const readUser = () => JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user') || 'null')
const authStore = (remember) => remember ? localStorage : sessionStorage

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readUser)
  const [loading, setLoading] = useState(false)
  const save = (data, remember = true) => { clearStoredAuth(); const store = authStore(remember); store.setItem('token', data.access_token); store.setItem('user', JSON.stringify(data.user)); setUser(data.user) }
  const login = async (email, password, remember = true) => save((await api.post('/api/auth/login', { email: email.trim().toLowerCase(), password })).data, remember)
  const register = async (payload, remember = true) => save((await api.post('/api/auth/register', { ...payload, email: payload.email.trim().toLowerCase() })).data, remember)
  const logout = () => { clearStoredAuth(); setUser(null) }
  useEffect(() => { if (getStoredToken()) api.get('/api/auth/me').then(r => { const remember = Boolean(localStorage.getItem('token')); authStore(remember).setItem('user', JSON.stringify(r.data)); setUser(r.data) }).catch(logout).finally(() => setLoading(false)) }, [])
  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>
}
export const useAuth = () => useContext(AuthContext)

import axios from 'axios'

export function getStoredToken() {
  return localStorage.getItem('token') || sessionStorage.getItem('token')
}

export function clearStoredAuth() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('user')
}

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' })
api.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
api.interceptors.response.use((r) => r, (e) => {
  if (e.response?.status === 401) { clearStoredAuth(); if (window.location.pathname !== '/login') window.location.href = '/login' }
  return Promise.reject(e)
})
export default api

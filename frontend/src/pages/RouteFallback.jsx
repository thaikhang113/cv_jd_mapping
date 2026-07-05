import { Link, Navigate, useRouteError } from 'react-router-dom'

export function RouteError() {
  const error = useRouteError()
  const message = error?.status === 404 ? 'Page not found' : (error?.message || 'Something went wrong')
  return <div className="auth-screen"><div className="auth-card" style={{ maxWidth: 520 }}><p className="eyebrow">CV Match Platform</p><h1>{message}</h1><p className="muted">The page may be missing, moved, or your session needs login.</p><div style={{ display: 'flex', gap: 12, marginTop: 20 }}><Link className="btn btn-primary" to="/login">Go to login</Link><Link className="btn" to="/candidate/jobs">Browse jobs</Link></div></div></div>
}

export function NotFound() {
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  return <Navigate to={user?.role ? `/${user.role}` : '/login'} replace />
}

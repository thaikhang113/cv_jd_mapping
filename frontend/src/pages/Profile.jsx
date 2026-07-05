import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function Profile() {
  const { user, updateProfile } = useAuth()
  const toast = useToast()
  const [name, setName] = useState(user?.name || '')
  const [saving, setSaving] = useState(false)
  useEffect(() => setName(user?.name || ''), [user?.name])
  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await updateProfile({ name })
      toast('Profile updated', 'success')
    } catch (e) {
      toast(e.response?.data?.detail || 'Update failed', 'error')
    } finally {
      setSaving(false)
    }
  }
  return <section><h1>Profile</h1><form onSubmit={submit} className="card form-grid" style={{maxWidth:640}}><div><label>Full name</label><input value={name} onChange={e=>setName(e.target.value)} placeholder="Your full name"/></div><div><label>Email</label><input value={user?.email || ''} disabled/></div><div><label>Role</label><input value={user?.role || ''} disabled/></div><button className="btn btn-primary" disabled={saving || !name.trim()}>{saving ? 'Saving...' : 'Save profile'}</button></form></section>
}

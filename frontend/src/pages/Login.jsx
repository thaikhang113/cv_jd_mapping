import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { LayoutDashboard } from 'lucide-react'

export default function Login() {
  const { login, user } = useAuth(); const nav = useNavigate(); const toast = useToast()
  const [form,setForm]=useState({email:'',password:''}); const [err,setErr]=useState(''); const [loading,setLoading]=useState(false)
  useEffect(()=>{if(user) nav('/'+user.role)},[user,nav])
  async function submit(e){e.preventDefault();setErr('');setLoading(true);try{await login(form.email,form.password);const u=JSON.parse(localStorage.getItem('user'));toast('Welcome back!','success');nav('/'+u.role)}catch(e){const m=e.response?.data?.detail||'Invalid credentials';setErr(m);toast(m,'error')}finally{setLoading(false)}}
  return <div className="auth"><div className="auth-card"><div className="auth-logo"><LayoutDashboard size={28}/></div><h1>Sign in</h1><p style={{margin:0,fontSize:'0.9rem',color:'var(--text-muted)'}}>Welcome to CV Match Platform</p><input placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/><input placeholder="Password" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>{err&&<p className="err">{err}</p>}<button disabled={loading} style={{justifyContent:'center',padding:14}}>{loading?'Signing in...':'Sign in'}</button><Link to="/register">Don&apos;t have an account? Create one</Link></div></div>
}
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { LayoutDashboard } from 'lucide-react'

export default function Login() {
  const { login, user } = useAuth(); const nav = useNavigate(); const toast = useToast()
  const [form,setForm]=useState({email:'',password:''}); const [remember,setRemember]=useState(true); const [err,setErr]=useState(''); const [loading,setLoading]=useState(false)
  useEffect(()=>{if(user) nav('/'+user.role)},[user,nav])
  const fillDemo = (role) => setForm(role === 'candidate' ? { email: 'candidate@example.com', password: 'Candidate123!' } : role === 'recruiter' ? { email: 'recruiter@example.com', password: 'Recruiter123!' } : { email: 'admin@example.com', password: 'Admin123!' })
  async function submit(e){e.preventDefault();setErr('');setLoading(true);try{await login(form.email,form.password,remember);const u=JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user'));toast('Welcome back!','success');nav('/'+u.role)}catch(e){const m=e.response?.data?.detail==='Invalid email or password'?'Sai email hoặc mật khẩu. Tài khoản mẫu dùng Candidate123! / Recruiter123! / Admin123!':(e.response?.data?.detail||'Invalid credentials');setErr(m);toast(m,'error')}finally{setLoading(false)}}
  return <div className="auth"><form onSubmit={submit} className="auth-card"><div className="auth-logo"><LayoutDashboard size={28}/></div><h1>Sign in</h1><p style={{margin:0,fontSize:'0.9rem',color:'var(--text-muted)'}}>Welcome to CV Match Platform</p><input placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/><input placeholder="Password" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/><label className="remember-row"><input type="checkbox" checked={remember} onChange={e=>setRemember(e.target.checked)}/> Lưu session trên máy này</label>{err&&<p className="err">{err}</p>}<button disabled={loading} style={{justifyContent:'center',padding:14}}>{loading?'Signing in...':'Sign in'}</button><div className="demo-logins"><span>Demo:</span><button type="button" onClick={()=>fillDemo('candidate')}>Candidate</button><button type="button" onClick={()=>fillDemo('recruiter')}>Recruiter</button><button type="button" onClick={()=>fillDemo('admin')}>Admin</button></div><Link to="/register">Don&apos;t have an account? Create one</Link></form></div>
}

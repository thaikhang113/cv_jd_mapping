import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { LayoutDashboard } from 'lucide-react'

export default function Register() {
  const { register } = useAuth(); const nav = useNavigate(); const toast = useToast()
  const [form,setForm]=useState({name:'',email:'',password:'',role:'candidate'}); const [err,setErr]=useState(''); const [loading,setLoading]=useState(false)
  async function submit(e){e.preventDefault();setErr('');setLoading(true);try{await register(form);const u=JSON.parse(localStorage.getItem('user'));toast('Account created!','success');nav('/'+u.role)}catch(e){const m=e.response?.data?.detail||'Registration failed';setErr(m);toast(m,'error')}finally{setLoading(false)}}
  return <div className="auth"><div className="auth-card"><div className="auth-logo"><LayoutDashboard size={28}/></div><h1>Create account</h1><p style={{margin:0,fontSize:'0.9rem',color:'var(--text-muted)'}}>Join the platform</p><input placeholder="Full name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/><input placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/><input placeholder="Password" type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/><select value={form.role} onChange={e=>setForm({...form,role:e.target.value})}><option value="candidate">Candidate</option><option value="recruiter">Recruiter</option></select>{err&&<p className="err">{err}</p>}<button disabled={loading} style={{justifyContent:'center',padding:14}}>{loading?'Creating...':'Create account'}</button><Link to="/login">Already have an account? Sign in</Link></div></div>
}
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
export default function Login() {
  const { login, user } = useAuth(); const nav = useNavigate(); const [form,setForm]=useState({email:'',password:''}); const [err,setErr]=useState('')
  if (user) nav(`/${user.role}`)
  async function submit(e){e.preventDefault(); setErr(''); try{await login(form.email,form.password); const u=JSON.parse(localStorage.getItem('user')); nav(`/${u.role}`)}catch(e){setErr(e.response?.data?.detail||'Login failed')}}
  return <div className="auth"><form onSubmit={submit}><h1>Login</h1><input placeholder="Email" onChange={e=>setForm({...form,email:e.target.value})}/><input placeholder="Password" type="password" onChange={e=>setForm({...form,password:e.target.value})}/><button>Login</button><p className="err">{err}</p><Link to="/register">Create account</Link></form></div>
}

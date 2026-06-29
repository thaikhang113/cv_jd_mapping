import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
export default function Register() {
  const { register } = useAuth(); const nav=useNavigate(); const [form,setForm]=useState({name:'',email:'',password:'',role:'candidate'}); const [err,setErr]=useState('')
  async function submit(e){e.preventDefault(); try{await register(form); const u=JSON.parse(localStorage.getItem('user')); nav(`/${u.role}`)}catch(e){setErr(e.response?.data?.detail||'Register failed')}}
  return <div className="auth"><form onSubmit={submit}><h1>Register</h1><input placeholder="Name" onChange={e=>setForm({...form,name:e.target.value})}/><input placeholder="Email" onChange={e=>setForm({...form,email:e.target.value})}/><input placeholder="Password" type="password" onChange={e=>setForm({...form,password:e.target.value})}/><select onChange={e=>setForm({...form,role:e.target.value})}><option value="candidate">Candidate</option><option value="recruiter">Recruiter</option></select><button>Register</button><p className="err">{err}</p><Link to="/login">Login</Link></form></div>
}

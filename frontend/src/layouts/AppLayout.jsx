import { useState, useEffect } from 'react'
import { Link, Outlet, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LayoutDashboard, Upload, FileText, Briefcase, ListChecks, MessageSquare, User, Users, BarChart3, Menu, Sun, Moon, LogOut } from 'lucide-react'
const menu = {
  candidate: [['/candidate','Dashboard',LayoutDashboard],['/candidate/upload-cv','Upload CV',Upload],['/candidate/cv','My CV',FileText],['/candidate/jobs','Matching Jobs',Briefcase],['/candidate/applications','Applications',ListChecks],['/messages','Messages',MessageSquare],['/profile','Profile',User]],
  recruiter: [['/recruiter','Dashboard',LayoutDashboard],['/recruiter/jobs/new','Create Job',Briefcase],['/recruiter/jobs','My Jobs',FileText],['/recruiter/upload-cvs','Upload CVs',Upload],['/recruiter/ranking','Ranking',BarChart3],['/recruiter/applications','Applications',ListChecks],['/messages','Messages',MessageSquare],['/profile','Profile',User]],
  admin: [['/admin','Dashboard',LayoutDashboard],['/admin/users','Users',Users],['/admin/cvs','CVs',FileText],['/admin/jobs','Jobs',Briefcase],['/admin/matches','Matches',BarChart3],['/admin/applications','Applications',ListChecks]],
}
export default function AppLayout() {
  const { user, logout } = useAuth(); const loc=useLocation(); const nav=useNavigate()
  const [so,setSo]=useState(false); const [dark,setDark]=useState(()=>localStorage.getItem('theme')==='dark')
  useEffect(()=>{document.documentElement.setAttribute('data-theme',dark?'dark':'light');localStorage.setItem('theme',dark?'dark':'light')},[dark])
  if(!user) return <Navigate to="/login" />
  return <div className="app">
    <div className={'sidebar-backdrop'+(so?' open':'')} onClick={()=>setSo(false)}/>
    <aside className={so?'open':''}>
      <div className="brand"><LayoutDashboard size={24}/><h2>CV Match</h2></div>
      <nav>{(menu[user.role]||[]).map(([to,label,Icon])=><Link key={to} to={to} className={loc.pathname===to||loc.pathname.startsWith(to+'/')?'active':''} onClick={()=>setSo(false)}><Icon size={18}/><span>{label}</span></Link>)}</nav>
    </aside>
    <main>
      <div className="topbar">
        <button className="hamburger" onClick={()=>setSo(true)}><Menu size={22}/></button>
        <div className="user-info"><div className="avatar">{user.name?user.name[0].toUpperCase():'?'}</div><span className="name-text">{user.name} · {user.role}</span></div>
        <div className="actions">
          <button className="theme-toggle" onClick={()=>setDark(d=>!d)}>{dark?<Sun size={18}/>:<Moon size={18}/>}</button>
          <button onClick={()=>{logout();nav('/login')}}><LogOut size={16} style={{marginRight:6}}/> Logout</button>
        </div>
      </div>
      <Outlet />
    </main>
  </div>
}

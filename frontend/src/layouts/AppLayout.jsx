import { Link, Outlet, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const menu = {
  candidate: [['/candidate','Dashboard'],['/candidate/upload-cv','Upload CV'],['/candidate/cv','My CV'],['/candidate/jobs','Matching Jobs'],['/candidate/applications','Applications'],['/messages','Messages'],['/profile','Profile']],
  recruiter: [['/recruiter','Dashboard'],['/recruiter/jobs/new','Create Job'],['/recruiter/jobs','My Jobs'],['/recruiter/upload-cvs','Upload CVs'],['/recruiter/ranking','Ranking'],['/recruiter/applications','Applications'],['/messages','Messages'],['/profile','Profile']],
  admin: [['/admin','Dashboard'],['/admin/users','Users'],['/admin/cvs','CVs'],['/admin/jobs','Jobs'],['/admin/matches','Matches'],['/admin/applications','Applications']]
}
export default function AppLayout() {
  const { user, logout } = useAuth()
  if (!user) return <Navigate to="/login" />
  return <div className="app"><aside><h2>CV Match</h2>{(menu[user.role] || []).map(([to,label]) => <Link key={to} to={to}>{label}</Link>)}</aside><main><nav><span>{user.name} · {user.role}</span><button onClick={logout}>Logout</button></nav><Outlet /></main></div>
}

import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
import { BarChart3, FileText, Briefcase, ListChecks, Users } from 'lucide-react'
const iconMap = { cvs:FileText, jobs:Briefcase, matching_results:BarChart3, applications:ListChecks, users:Users }
const colorMap = { cvs:'card-primary', jobs:'card-warning', matching_results:'card-info', applications:'card-success', users:'card-primary' }
export default function Dashboard({ role }) {
  const [stats,setStats]=useState(null); const [loading,setLoading]=useState(true)
  useEffect(()=>{if(role==='admin'){api.get('/api/admin/stats').then(r=>{setStats(r.data);setLoading(false)}).catch(()=>setLoading(false))}else setLoading(false)},[role])
  if(loading) return <section><h1>{role.charAt(0).toUpperCase()+role.slice(1)} Dashboard</h1><div className="cards">{[1,2,3,4].map(i=><div key={i} className="card" style={{height:140}}><div className="skeleton" style={{width:40,height:40,borderRadius:10,marginBottom:12}}/><div className="skeleton" style={{width:'60%',height:28,marginBottom:8}}/><div className="skeleton" style={{width:'40%',height:14}}/></div>)}</div></section>
  const items = stats ? Object.entries(stats).filter(([k])=>k!=='conversations') : [['cvs','—'],['jobs','—'],['applications','—'],['users','—']]
  return <section><h1>{role.charAt(0).toUpperCase()+role.slice(1)} Dashboard</h1>
    <div className="cards">{items.map(([k,v])=>{const Icon=iconMap[k]||BarChart3;return <div key={k} className={'card '+(colorMap[k]||'card-primary')}><div className="card-icon"><Icon size={20}/></div><div className="card-value">{v}</div><div className="card-label">{k.replace(/_/g,' ')}</div></div>})}</div>
  </section>
}
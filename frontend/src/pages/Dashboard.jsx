import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
export default function Dashboard({ role }) { const [stats,setStats]=useState(null); useEffect(()=>{ if(role==='admin') api.get('/api/admin/stats').then(r=>setStats(r.data)).catch(()=>{})},[role]); return <section><h1>{role} Dashboard</h1><div className="cards">{stats?Object.entries(stats).map(([k,v])=><div className="card" key={k}><b>{v}</b><span>{k}</span></div>):['CVs','Jobs','Matches','Messages'].map(x=><div className="card" key={x}>{x}</div>)}</div></section> }

import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
import { BarChart3 } from 'lucide-react'

function ProgressBar({ score }) {
  const cls = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low'
  const label = score >= 80 ? 'Strong Match' : score >= 60 ? 'Good Match' : 'Weak Match'
  const badge = score >= 80 ? 'badge-success' : score >= 60 ? 'badge-warning' : 'badge-danger'
  return <div><div style={{display:'flex',justifyContent:'space-between',marginBottom:4,fontSize:'0.85rem'}}><span style={{fontWeight:600}}>{score}%</span><span className={'badge '+badge}>{label}</span></div><div className="progress-track"><div className={'progress-fill '+cls} style={{width:score+'%'}}/></div></div>
}

export default function Ranking() {
  const [jobs,setJobs]=useState([]); const [job,setJob]=useState(''); const [rows,setRows]=useState([]); const [run,setRun]=useState(false)
  useEffect(()=>{api.get('/api/jobs/my').then(r=>setJobs(r.data))},[])
  async function runMatch(){setRun(true);const r=await api.post('/api/matches/run',{job_id:job});setRows(r.data);setRun(false)}
  return <section><h1>Candidate Ranking</h1>
    <div style={{display:'flex',gap:12,marginBottom:24}}><select value={job} onChange={e=>setJob(e.target.value)} style={{maxWidth:400}}><option value="">Select a job</option>{jobs.map(j=><option key={j.id} value={j.id}>{j.title}</option>)}</select><button className="btn btn-primary" disabled={!job||run} onClick={runMatch}>{run?'Running...':'Run Matching'}</button></div>
    {rows.length===0 ? <div className="empty-state"><BarChart3 size={48} strokeWidth={1.5}/><h3>No matching results</h3><p>Select a job and click Run Matching to see ranking</p></div>
    : <div className="table-wrap"><table><thead><tr><th>Rank</th><th>Score</th><th>Matched Skills</th><th>Missing Skills</th><th>Match</th></tr></thead><tbody>{rows.map((r,i)=><tr key={r.cv_id}><td style={{fontWeight:700,fontFamily:'Poppins'}}>#{r.rank||i+1}</td><td style={{minWidth:200}}><ProgressBar score={Math.round(r.overall_score)}/></td><td>{(r.matched_skills||[]).map(s=><span key={s} className="badge badge-success" style={{marginRight:4,marginBottom:2}}>{s}</span>)}</td><td>{(r.missing_skills||[]).map(s=><span key={s} className="badge badge-danger" style={{marginRight:4,marginBottom:2}}>{s}</span>)}</td><td>{r.experience_match?'✅ Yrs ✓':'❌ Yrs ✗'} {r.location_match?'📍 Match':'📍 No'}</td></tr>)}</tbody></table></div>}
  </section>
}
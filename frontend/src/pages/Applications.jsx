import { useEffect, useMemo, useState } from 'react'
import api from '../api/axiosClient'

function scoreLabel(score) {
  if (score == null) return { text: 'Not matched yet', cls: 'badge' }
  if (score >= 80) return { text: 'Strong Match', cls: 'badge badge-success' }
  if (score >= 60) return { text: 'Good Match', cls: 'badge badge-warning' }
  return { text: 'Weak Match', cls: 'badge badge-danger' }
}

export default function Applications() {
  const [rows,setRows]=useState([])
  const [matches,setMatches]=useState([])
  useEffect(()=>{Promise.all([api.get('/api/applications/my'),api.get('/api/matches/my')]).then(([apps,matchRows])=>{setRows(apps.data);setMatches(matchRows.data)})},[])
  const matchByJob = useMemo(() => matches.reduce((acc,m) => { if (!acc[m.job_id] || m.overall_score > acc[m.job_id].overall_score) acc[m.job_id] = m; return acc }, {}), [matches])
  return <section><h1>Applications Management</h1><table><thead><tr><th>Job</th><th>Candidate</th><th>Status</th><th>Matching Score</th></tr></thead><tbody>{rows.map(a=>{const m=matchByJob[a.job_id];const label=scoreLabel(m?.overall_score);return <tr key={a.id}><td>{a.job_id}</td><td>{a.candidate_id}</td><td>{a.status}</td><td>{m ? <><b>{Math.round(m.overall_score)}%</b> <span className={label.cls}>{label.text}</span></> : <span className="badge">{label.text}</span>}</td></tr>})}</tbody></table></section>
}

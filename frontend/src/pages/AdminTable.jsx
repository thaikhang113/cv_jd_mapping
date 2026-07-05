import { useEffect, useState } from 'react'
import api from '../api/axiosClient'

function value(v) { return Array.isArray(v) ? v.join(', ') : String(v ?? '') }

export default function AdminTable({ type }) {
  const [rows,setRows]=useState([])
  useEffect(()=>{api.get(`/api/admin/${type}`).then(r=>setRows(r.data))},[type])
  if (type === 'applications') return <section><h1>Manage applications</h1><table><thead><tr><th>Job</th><th>Candidate</th><th>Recruiter</th><th>Status</th><th>CV</th></tr></thead><tbody>{rows.map(row=><tr key={row.id}><td><b>{row.job_title || row.job_id}</b><br/><span className="muted">{row.company_name}</span></td><td>{row.candidate_name || row.candidate_id}</td><td>{row.recruiter_name || row.recruiter_id}</td><td><span className="badge">{row.status}</span></td><td>{row.cv_id}</td></tr>)}</tbody></table></section>
  if (type === 'matches') return <section><h1>Manage matches</h1><table><thead><tr><th>Rank</th><th>Score</th><th>Matched Skills</th><th>Missing Skills</th><th>CV</th></tr></thead><tbody>{rows.map(row=><tr key={row.id || `${row.job_id}-${row.cv_id}`}><td>#{row.rank || '-'}</td><td><b>{Math.round(row.overall_score || 0)}%</b></td><td>{value(row.matched_skills)}</td><td>{value(row.missing_skills)}</td><td>{row.cv_id}</td></tr>)}</tbody></table></section>
  return <section><h1>Manage {type}</h1><table><tbody>{rows.map(row=><tr key={row.id}>{Object.entries(row).slice(0,6).map(([k,v])=><td key={k}><small>{k}</small><br/>{value(v)}</td>)}</tr>)}</tbody></table></section>
}

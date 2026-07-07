import { Link, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
import { useToast } from '../context/ToastContext'
import MatchReport from '../components/MatchReport'

export default function Jobs({ mine=false }) {
  const [rows,setRows]=useState([])
  const [matches,setMatches]=useState([])
  const [selected,setSelected]=useState(null)
  const toast=useToast(); const navigate=useNavigate()
  useEffect(()=>{api.get(mine?'/api/jobs/my':'/api/jobs').then(r=>setRows(r.data)); if (!mine) api.get('/api/matches/my').then(r=>setMatches(r.data)).catch(()=>setMatches([]))},[mine])
  async function messageRecruiter(job) {
    try { const r=await api.post('/api/conversations',{participant_id:job.recruiter_id,job_id:job.id}); navigate(`/messages?conversation=${r.data.id}`) }
    catch(e) { toast(e.response?.data?.detail || 'Cannot open conversation','error') }
  }
  return <section><h1>{mine?'My Jobs':'Matching Jobs'}</h1><div className="table-wrap"><table><thead><tr><th>Job</th><th>Location</th><th>Skills</th>{!mine&&<th>Fit</th>}<th>Actions</th></tr></thead><tbody>{rows.map(j=>{const match=matches.find(m=>m.job_id===j.id);return <tr key={j.id}><td><b><Link to={mine ? `/recruiter/jobs/${j.id}` : `/candidate/jobs/${j.id}`}>{j.title}</Link></b><br/><span className="muted">{j.company_name}</span></td><td>{j.location}</td><td>{(j.required_skills||[]).join(', ')}</td>{!mine&&<td>{match ? <button type="button" className="btn btn-primary btn-sm" onClick={()=>setSelected({match, job:j})}>{Math.round(match.overall_score)}% report</button> : <span className="badge">Chưa có match</span>}</td>}<td><div className="row-actions"><Link className="btn btn-secondary btn-sm" to={mine ? `/recruiter/jobs/${j.id}` : `/candidate/jobs/${j.id}`}>View JD</Link>{!mine&&j.recruiter_id&&<button className="btn btn-primary btn-sm" onClick={()=>messageRecruiter(j)}>Message recruiter</button>}</div></td></tr>})}</tbody></table></div>{selected&&<MatchReport match={selected.match} jobTitle={selected.job.title} companyName={selected.job.company_name} onClose={()=>setSelected(null)} />}</section>
}

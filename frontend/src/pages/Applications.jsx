import { useEffect, useMemo, useState } from 'react'
import api from '../api/axiosClient'

function scoreLabel(score) {
  if (score == null) return { text: 'Not matched yet', cls: 'badge' }
  if (score >= 80) return { text: 'Strong Match', cls: 'badge badge-success' }
  if (score >= 60) return { text: 'Good Match', cls: 'badge badge-warning' }
  return { text: 'Weak Match', cls: 'badge badge-danger' }
}

function MatchDetail({ match }) {
  if (!match) return <span className="badge">Recruiter has not run matching yet</span>
  const label = scoreLabel(match.overall_score)
  return <div className="match-detail">
    <div><b>{Math.round(match.overall_score)}%</b> <span className={label.cls}>{label.text}</span></div>
    <div className="muted">Skill {Math.round(match.skill_score || 0)}/40 · Experience {Math.round(match.experience_score || 0)}/20 · Location {Math.round(match.location_score || 0)}/10 · Text {Math.round(match.similarity_score || 0)}/30</div>
    <div className="muted">{match.experience_match ? 'Experience matched' : 'Experience gap'} · {match.location_match ? 'Location matched' : 'Location not matched'}</div>
    <div>{(match.matched_skills || []).slice(0, 6).map(s => <span key={s} className="badge badge-success" style={{marginRight:4,marginTop:4}}>{s}</span>)}</div>
    {(match.missing_skills || []).length > 0 && <div>{match.missing_skills.slice(0, 6).map(s => <span key={s} className="badge badge-danger" style={{marginRight:4,marginTop:4}}>{s}</span>)}</div>}
  </div>
}

export default function Applications() {
  const [rows,setRows]=useState([])
  const [matches,setMatches]=useState([])
  useEffect(()=>{Promise.all([api.get('/api/applications/my'),api.get('/api/matches/my')]).then(([apps,matchRows])=>{setRows(apps.data);setMatches(matchRows.data)})},[])
  const matchesByApp = useMemo(() => matches.reduce((acc,m) => { acc[`${m.job_id}:${m.cv_id}`] = m; if (!acc[m.job_id] || m.overall_score > acc[m.job_id].overall_score) acc[m.job_id] = m; return acc }, {}), [matches])
  return <section><h1>Applications Management</h1><table><thead><tr><th>Job</th><th>Candidate</th><th>Status</th><th>Matching Detail</th></tr></thead><tbody>{rows.map(a=>{const match=matchesByApp[`${a.job_id}:${a.cv_id}`] || matchesByApp[a.job_id];return <tr key={a.id}><td><b>{a.job_title || a.job_id}</b><br/><span className="muted">{a.company_name}</span></td><td>{a.candidate_name || a.candidate_id}</td><td><span className="badge">{a.status}</span></td><td><MatchDetail match={match}/></td></tr>})}</tbody></table></section>
}

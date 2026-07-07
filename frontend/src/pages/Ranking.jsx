import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
import { BarChart3 } from 'lucide-react'
import MatchReport from '../components/MatchReport'

const EMPTY = []
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))
function ProgressBar({ score }) {
  const cls = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low'
  const label = score >= 80 ? 'Strong Match' : score >= 60 ? 'Good Match' : 'Weak Match'
  const badge = score >= 80 ? 'badge-success' : score >= 60 ? 'badge-warning' : 'badge-danger'
  return <div><div style={{display:'flex',justifyContent:'space-between',marginBottom:4,fontSize:'0.85rem'}}><span style={{fontWeight:600}}>{score}%</span><span className={'badge '+badge}>{label}</span></div><div className="progress-track"><div className={'progress-fill '+cls} style={{width:score+'%'}}/></div></div>
}
function Badges({ values = EMPTY, cls = 'badge' }) { return values.length ? values.slice(0, 8).map(s => <span key={s} className={cls} style={{marginRight:4,marginBottom:2}}>{s}</span>) : <span className="muted">No skills detected</span> }
function MatchRunProgress({ run }) {
  if (!run) return null
  const total = run.total || 0
  const processed = run.processed || 0
  const percent = run.percent ?? (total ? Math.round((processed / total) * 100) : 0)
  return <div className="batch-progress-grid" style={{marginBottom:24}}>
    <div className="upload-progress">
      <div className="upload-progress-meta"><span>Matching: {processed}/{total}</span><b>{percent}%</b></div>
      <div className="progress-track"><div className={`progress-fill ${run.status === 'failed' ? 'failed' : run.status === 'done' ? 'complete' : 'active'}`} style={{width:`${percent}%`}} /></div>
    </div>
  </div>
}

export default function Ranking() {
  const [jobs,setJobs]=useState([]); const [job,setJob]=useState(''); const [rows,setRows]=useState([]); const [run,setRun]=useState(false); const [selected,setSelected]=useState(null); const [runState,setRunState]=useState(null); const [error,setError]=useState('')
  useEffect(()=>{api.get('/api/jobs/my').then(r=>setJobs(r.data))},[])
  useEffect(()=>{if(!job){setRows([]);setSelected(null);return} api.get(`/api/matches/job/${job}`).then(r=>{setRows(r.data);setSelected(r.data[0]||null)}).catch(()=>{})},[job])
  const selectedJob = jobs.find(j => j.id === job)
  async function runMatch(){
    setRun(true); setError('')
    try {
      const created = (await api.post('/api/matches/run',{job_id:job})).data
      setRunState(created)
      for (let i = 0; i < 180; i++) {
        await sleep(1500)
        const state = (await api.get(`/api/matches/run/${created.run_id}`)).data
        setRunState(state)
        if (state.status === 'done') {
          setRows(state.results || [])
          setSelected((state.results || [])[0] || null)
          return
        }
        if (state.status === 'failed') throw new Error(state.error || 'Matching failed')
      }
      throw new Error('Matching timeout')
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Matching failed')
    } finally {
      setRun(false)
    }
  }
  return <section><h1>Candidate Ranking</h1>
    <div style={{display:'flex',gap:12,marginBottom:24}}><select value={job} onChange={e=>setJob(e.target.value)} style={{maxWidth:400}}><option value="">Select a job</option>{jobs.map(j=><option key={j.id} value={j.id}>{j.title}</option>)}</select><button type="button" className="btn btn-primary" disabled={!job||run} onClick={runMatch}>{run?'Running...':'Run Matching'}</button></div>
    <MatchRunProgress run={runState} />
    {error&&<div className="toast error" style={{position:'static',marginBottom:16}}>{error}</div>}
    {rows.length===0 ? <div className="empty-state"><BarChart3 size={48} strokeWidth={1.5}/><h3>No matching results</h3><p>Select a job and click Run Matching to see ranking</p></div>
    : <><div className="table-wrap"><table><thead><tr><th>Rank</th><th>Score</th><th>Candidate</th><th>CV Skills</th><th>Matched / Missing</th><th>Match</th><th>Report</th></tr></thead><tbody>{rows.map((r,i)=><tr key={r.cv_id} className={selected?.cv_id===r.cv_id?'selected-row':''}><td style={{fontWeight:700,fontFamily:'Poppins'}}>#{r.rank||i+1}</td><td style={{minWidth:200}}><ProgressBar score={Math.round(r.overall_score)}/></td><td><b>{r.cv_name || r.candidate_name || 'Candidate'}</b><br/><span className="muted">{r.cv_email || 'No email'} - {r.cv_phone || 'No phone'}</span><br/><span className="muted">{r.cv_filename}</span></td><td><Badges values={r.cv_skills || []} cls="badge" /></td><td><Badges values={r.matched_skills||[]} cls="badge badge-success" />{(r.missing_skills||[]).length>0&&<div style={{marginTop:4}}><Badges values={r.missing_skills||[]} cls="badge badge-danger" /></div>}</td><td>{r.experience_match?'Yrs OK':'Yrs gap'} - {r.location_match?'Location OK':'Location gap'}</td><td><button type="button" className="btn btn-primary btn-sm" onClick={()=>setSelected(r)}>Xem report</button></td></tr>)}</tbody></table></div>{selected&&<MatchReport match={selected} jobTitle={selectedJob?.title} companyName={selectedJob?.company_name} />}</>}
  </section>
}

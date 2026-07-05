import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api/axiosClient'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const splitComma = value => String(value || '').split(',').flatMap(x => { const item = x.trim(); return item ? [item] : [] })
const joinComma = value => (value || []).join(', ')
const toForm = data => ({ title:data.title||'', company_name:data.company_name||'', location:data.location||'', required_skills:joinComma(data.required_skills), nice_to_have_skills:joinComma(data.nice_to_have_skills), required_experience:data.required_experience||0, salary_range:data.salary_range||'', description:data.description||'', status:data.status||'open' })

export default function JobDetail() {
  const { jobId } = useParams()
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [form, setForm] = useState(null)
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [applying, setApplying] = useState(false)
  const [openingChat, setOpeningChat] = useState(false)
  const canManage = useMemo(() => user?.role === 'admin' || (user?.role === 'recruiter' && job?.recruiter_id === user?.id), [user, job])

  useEffect(() => { api.get(`/api/jobs/${jobId}`).then(r => { setJob(r.data); setForm(toForm(r.data)) }).catch(() => toast('Job not found', 'error')).finally(() => setLoading(false)) }, [jobId, toast])
  function payload() { return { ...form, required_skills:splitComma(form.required_skills), nice_to_have_skills:splitComma(form.nice_to_have_skills), required_experience:Number(form.required_experience||0), responsibilities:job?.responsibilities||[], requirements:job?.requirements||[], benefits:job?.benefits||[], category:job?.category||null, seniority:job?.seniority||null, job_type:job?.job_type||null, work_mode:job?.work_mode||null, raw_text:job?.raw_text||null, parsed_sections:job?.parsed_sections||{}, parse_confidence:Number(job?.parse_confidence||0) } }
  async function apply() { setApplying(true); try { await api.post('/api/applications', { job_id: jobId }); toast('Applied with primary CV','success'); navigate('/candidate/applications') } catch (e) { toast(e.response?.data?.detail || 'Apply failed','error') } finally { setApplying(false) } }
  async function messageRecruiter() { setOpeningChat(true); try { const r=await api.post('/api/conversations',{participant_id:job.recruiter_id,job_id:job.id}); navigate(`/messages?conversation=${r.data.id}`) } catch(e) { toast(e.response?.data?.detail || 'Cannot open conversation','error') } finally { setOpeningChat(false) } }
  async function saveJob(e) { e.preventDefault(); setSaving(true); try { const r=await api.put(`/api/jobs/${jobId}`, payload()); setJob(r.data); setForm(toForm(r.data)); setEditing(false); toast('Job updated','success') } catch(e) { toast(e.response?.data?.detail || 'Failed to update job','error') } finally { setSaving(false) } }
  async function deleteJob() { if (!confirm(`Delete ${job.title}?`)) return; setSaving(true); try { await api.delete(`/api/jobs/${jobId}`); toast('Job deleted','success'); navigate(user?.role === 'admin' ? '/admin/jobs' : '/recruiter/jobs') } catch(e) { toast(e.response?.data?.detail || 'Failed to delete job','error') } finally { setSaving(false) } }

  if (loading) return <section><h1>Loading job...</h1></section>
  if (!job) return <section><h1>Job not found</h1><Link className="btn" to="/candidate/jobs">Back to jobs</Link></section>
  if (editing && form) return <section className="detail-page"><div className="page-head"><div><p className="eyebrow">Edit job</p><h1>{job.title}</h1></div><span className="badge">{job.status}</span></div><form onSubmit={saveJob} className="form-grid">{['title','company_name','location','required_skills','nice_to_have_skills','required_experience','salary_range','status'].map(k=><div key={k}><label>{k.replace(/_/g,' ')}<input placeholder={k} type={k==='required_experience'?'number':'text'} value={form[k]??''} onChange={e=>setForm({...form,[k]:e.target.value})}/></label></div>)}<div><label>Description<textarea rows={6} placeholder="Description" value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label></div><div className="row-actions"><button type="submit" className="btn btn-primary" disabled={saving}>{saving?'Saving...':'Save job'}</button><button type="button" className="btn btn-secondary" onClick={()=>{setEditing(false);setForm(toForm(job))}}>Cancel</button></div></form></section>
  return <section className="detail-page"><div className="page-head"><div><p className="eyebrow">Job description</p><h1>{job.title}</h1><p className="muted">{job.company_name} · {job.location}</p></div><span className="badge">{job.status}</span></div><div className="grid two"><div className="card"><h2>Requirements</h2><p><b>Skills:</b> {(job.required_skills || []).join(', ') || 'Not specified'}</p><p><b>Nice to have:</b> {(job.nice_to_have_skills || []).join(', ') || '?'}</p><p><b>Experience:</b> {job.required_experience || 0}+ years</p><p><b>Category:</b> {job.category || '?'} · <b>Seniority:</b> {job.seniority || '?'} · <b>Mode:</b> {job.work_mode || '?'}</p><p><b>Salary:</b> {job.salary_range || 'Negotiable'}</p></div><div className="card"><h2>Job description</h2><p style={{ whiteSpace: 'pre-wrap' }}>{job.description}</p>{(job.responsibilities||[]).length>0&&<><h3>Responsibilities</h3><ul>{job.responsibilities.map(x=><li key={x}>{x}</li>)}</ul></>}{(job.requirements||[]).length>0&&<><h3>Requirements</h3><ul>{job.requirements.map(x=><li key={x}>{x}</li>)}</ul></>}{(job.benefits||[]).length>0&&<><h3>Benefits</h3><ul>{job.benefits.map(x=><li key={x}>{x}</li>)}</ul></>}</div></div><div className="row-actions detail-actions">{user?.role === 'candidate' && <button type="button" className="btn btn-primary" disabled={applying || job.status !== 'open'} onClick={apply}>{applying ? 'Applying...' : 'Apply with primary CV'}</button>}{user?.role === 'candidate' && job.recruiter_id && <button type="button" className="btn btn-secondary" disabled={openingChat} onClick={messageRecruiter}>{openingChat?'Opening...':'Message recruiter'}</button>}{user?.role === 'recruiter' && <Link className="btn btn-primary" to="/recruiter/ranking">View ranking</Link>}{canManage&&<button type="button" className="btn btn-secondary" onClick={()=>setEditing(true)}>Edit job</button>}{canManage&&<button type="button" className="btn btn-secondary" disabled={saving} onClick={deleteJob}>Delete job</button>}</div></section>
}

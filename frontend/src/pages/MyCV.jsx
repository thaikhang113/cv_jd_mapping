import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const skillsText = cv => (cv.extracted_data?.skills || []).join(', ') || 'No skills detected yet'

export default function MyCV() {
  const { user, updateProfile } = useAuth()
  const toast = useToast()
  const [rows,setRows]=useState([])
  const [saving,setSaving]=useState('')
  useEffect(()=>{api.get('/api/cvs/my').then(r=>setRows(r.data))},[])
  async function setPrimary(cv) {
    setSaving(cv.id)
    try { await updateProfile({ primary_cv_id: cv.id }); setRows(prev=>prev.map(row=>({...row,is_primary:row.id===cv.id}))); toast('Primary CV selected','success') }
    catch(e) { toast(e.response?.data?.detail || 'Failed to set primary CV','error') }
    finally { setSaving('') }
  }
  async function deleteCv(cv) {
    if (!confirm(`Delete ${cv.filename}?`)) return
    setSaving(cv.id)
    try { await api.delete(`/api/cvs/${cv.id}`); setRows(prev=>prev.filter(row=>row.id!==cv.id)); toast('CV deleted','success') }
    catch(e) { toast(e.response?.data?.detail || 'Failed to delete CV','error') }
    finally { setSaving('') }
  }
  return <section><div className="page-head"><div><p className="eyebrow">Candidate profile</p><h1>My CV Profile</h1><p className="muted">Latest uploaded CV becomes current CV automatically after parsing.</p></div></div>{rows.length===0?<div className="empty-state"><h3>No CV uploaded</h3><p>Upload a PDF/DOCX first. Email, phone and skills will appear here after parsing.</p></div>:<div className="cv-grid">{rows.map(cv=>{const primary=cv.is_primary||user?.primary_cv_id===cv.id;const done=cv.processing_status==='done';const failed=cv.processing_status==='failed';return <div className={'card cv-card'+(primary?' primary':'')} key={cv.id}><div className="cv-card-head"><h3>{cv.filename}</h3>{primary&&<span className="badge badge-success">Current CV</span>}</div><p><b>Name:</b> {cv.extracted_data?.name || 'Not detected'}</p><p><b>Email:</b> {cv.extracted_data?.email || 'Not detected'} - <b>Phone:</b> {cv.extracted_data?.phone || 'Not detected'}</p><p><b>Status:</b> <span className={failed?'badge badge-danger':'badge'}>{cv.processing_status || 'done'}</span></p>{cv.processing_error&&<p className="err">{cv.processing_error}</p>}{cv.matching_error&&<p className="muted">Matching warning: {cv.matching_error}</p>}<p><b>Experience:</b> {cv.extracted_data?.experience_years ?? '-'} years - <b>Jobs:</b> {(cv.extracted_data?.work_experiences||[]).length} - <b>Projects:</b> {(cv.extracted_data?.projects||[]).length}</p><p><b>Skills:</b> {skillsText(cv)}</p>{(cv.extracted_data?.work_experiences||[]).slice(0,2).map(x=><p key={(x.role||'')+(x.company||'')} className="muted">{x.role} - {x.company}</p>)}<div className="row-actions"><button type="button" className="btn btn-primary" disabled={!done||primary||saving===cv.id} onClick={()=>setPrimary(cv)}>{primary?'Selected':saving===cv.id?'Saving...':'Set as current CV'}</button><button type="button" className="btn btn-secondary" disabled={saving===cv.id} onClick={()=>deleteCv(cv)}>Delete CV</button></div>{!done&&!failed&&<p className="muted">Parsing CV. You can apply after status becomes done.</p>}</div>})}</div>}</section>
}

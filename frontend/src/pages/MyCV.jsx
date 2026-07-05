import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function MyCV() {
  const { user, updateProfile } = useAuth()
  const toast = useToast()
  const [rows,setRows]=useState([])
  const [saving,setSaving]=useState('')
  useEffect(()=>{api.get('/api/cvs/my').then(r=>setRows(r.data))},[])
  async function setPrimary(cv) {
    setSaving(cv.id)
    try { await updateProfile({ primary_cv_id: cv.id }); toast('Primary CV selected','success') }
    catch(e) { toast(e.response?.data?.detail || 'Failed to set primary CV','error') }
    finally { setSaving('') }
  }
  return <section><div className="page-head"><div><p className="eyebrow">Candidate profile</p><h1>My CV Profile</h1><p className="muted">Choose the CV used by default when applying for jobs.</p></div></div>{rows.length===0?<div className="empty-state"><h3>No CV uploaded</h3><p>Upload a PDF/DOCX first, then select it as your primary CV.</p></div>:<div className="cv-grid">{rows.map(cv=>{const primary=user?.primary_cv_id===cv.id;const done=cv.processing_status==='done';return <div className={'card cv-card'+(primary?' primary':'')} key={cv.id}><div className="cv-card-head"><h3>{cv.filename}</h3>{primary&&<span className="badge badge-success">Primary CV</span>}</div><p className="muted">{cv.extracted_data?.email || 'No email'} · {cv.extracted_data?.phone || 'No phone'}</p><p><b>Status:</b> <span className="badge">{cv.processing_status || 'done'}</span></p><p><b>Experience:</b> {cv.extracted_data?.experience_years ?? '—'} years</p><p><b>Skills:</b> {(cv.extracted_data?.skills||[]).join(', ') || 'Extracting skills...'}</p><button className="btn btn-primary" disabled={!done||primary||saving===cv.id} onClick={()=>setPrimary(cv)}>{primary?'Selected':saving===cv.id?'Saving...':'Set as primary CV'}</button>{!done&&<p className="muted">Wait until processing is done before selecting this CV.</p>}</div>})}</div>}</section>
}

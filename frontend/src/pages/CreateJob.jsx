import { useState } from 'react'
import { Upload, Sparkles } from 'lucide-react'
import api from '../api/axiosClient'
import { useToast } from '../context/ToastContext'

const emptyForm = {title:'',company_name:'',location:'',required_skills:'',nice_to_have_skills:'',required_experience:0,salary_range:'',description:'',status:'open',category:'',seniority:'',job_type:'',work_mode:'',responsibilities:'',requirements:'',benefits:''}
const listText = v => Array.isArray(v) ? v.join(', ') : (v || '')
const linesText = v => Array.isArray(v) ? v.join('\n') : (v || '')
const splitComma = v => v.split(',').flatMap(s => { const item = s.trim(); return item ? [item] : [] })
const splitLines = v => v.split('\n').flatMap(s => { const item = s.trim(); return item ? [item] : [] })

export default function CreateJob() {
  const toast = useToast()
  const [form,setForm]=useState(emptyForm)
  const [parsing,setParsing]=useState(false)
  const [draft,setDraft]=useState(null)

  function applyDraft(d) {
    setDraft(d)
    setForm({
      title:d.title||'', company_name:d.company_name||'', location:d.location||'', required_skills:listText(d.required_skills), nice_to_have_skills:listText(d.nice_to_have_skills),
      required_experience:d.required_experience||0, salary_range:d.salary_range||'', description:d.description||'', status:d.status||'open', category:d.category||'', seniority:d.seniority||'', job_type:d.job_type||'', work_mode:d.work_mode||'',
      responsibilities:linesText(d.responsibilities), requirements:linesText(d.requirements), benefits:linesText(d.benefits), raw_text:d.raw_text||'', parsed_sections:d.parsed_sections||{}, parse_confidence:d.parse_confidence||0
    })
  }

  async function parseFile(e){
    const file=e.target.files?.[0]
    if(!file)return
    const fd=new FormData(); fd.append('file',file)
    setParsing(true)
    try{const r=await api.post('/api/jobs/parse-document',fd); applyDraft(r.data.draft); toast(`JD extracted: ${Math.round(r.data.draft.parse_confidence||0)}% confidence`,'success')}
    catch(e){toast(e.response?.data?.detail||'JD parse failed','error')}
    finally{setParsing(false); e.target.value=''}
  }

  async function submit(e){
    e.preventDefault()
    const payload={...form,
      required_skills:splitComma(form.required_skills),
      nice_to_have_skills:splitComma(form.nice_to_have_skills),
      required_experience:Number(form.required_experience||0),
      responsibilities:splitLines(form.responsibilities),
      requirements:splitLines(form.requirements),
      benefits:splitLines(form.benefits),
      parse_confidence:Number(form.parse_confidence||0)
    }
    try{await api.post('/api/jobs',payload);toast('Job created!','success');setForm(emptyForm);setDraft(null)}catch(e){toast(e.response?.data?.detail||'Failed to create job','error')}
  }

  return <section><div className="page-head"><div><p className="eyebrow">Recruiter workflow</p><h1>Create Job</h1><p className="muted">Upload JD PDF/DOCX to auto-fill, review, then publish.</p></div></div>
    <label className="upload-zone" htmlFor="jdInput" style={{cursor:'pointer',marginBottom:16}}><Upload size={32}/><p>{parsing?'Extracting JD...':'Drop JD here or browse PDF/DOCX'}</p><p style={{marginTop:8,fontSize:'0.8rem'}}>Traditional parser: sections, skills, experience, category, seniority</p></label>
    <input id="jdInput" type="file" accept=".pdf,.docx" style={{display:'none'}} onChange={parseFile}/>
    {draft&&<div className="card" style={{marginBottom:16}}><h3><Sparkles size={18}/> Extracted JD draft</h3><p className="muted">Confidence: {Math.round(draft.parse_confidence||0)}% ? Category: {draft.category||'-'} ? Seniority: {draft.seniority||'-'} ? Work mode: {draft.work_mode||'-'}</p><div>{(draft.required_skills||[]).map(s=><span key={s} className="badge badge-success" style={{marginRight:4}}>{s}</span>)}{(draft.nice_to_have_skills||[]).map(s=><span key={s} className="badge" style={{marginRight:4}}>{s}</span>)}</div></div>}
    <form onSubmit={submit} className="form-grid">
      {['title','company_name','location','required_skills','nice_to_have_skills','required_experience','salary_range','category','seniority','job_type','work_mode'].map(k=><div key={k}><label>{k.replace(/_/g,' ')}<input placeholder={k} value={form[k]??''} onChange={e=>setForm({...form,[k]:e.target.value})} type={k==='required_experience'?'number':'text'}/></label></div>)}
      <div><label>Description<textarea rows={5} placeholder="Description" value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label></div>
      <div><label>Responsibilities<textarea rows={4} placeholder="One per line" value={form.responsibilities} onChange={e=>setForm({...form,responsibilities:e.target.value})}/></label></div>
      <div><label>Requirements<textarea rows={4} placeholder="One per line" value={form.requirements} onChange={e=>setForm({...form,requirements:e.target.value})}/></label></div>
      <div><label>Benefits<textarea rows={4} placeholder="One per line" value={form.benefits} onChange={e=>setForm({...form,benefits:e.target.value})}/></label></div>
      <button type="submit" className="btn btn-primary" style={{justifyContent:'center',padding:14}}>Create Job</button>
    </form></section>
}

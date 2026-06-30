import { useState } from 'react'
import api from '../api/axiosClient'
import { useToast } from '../context/ToastContext'
export default function CreateJob() {
  const toast = useToast()
  const [form,setForm]=useState({title:'',company_name:'',location:'',required_skills:'',required_experience:0,salary_range:'',description:'',status:'open'})
  async function submit(e){e.preventDefault();try{await api.post('/api/jobs',{...form,required_skills:form.required_skills.split(',').map(s=>s.trim()).filter(Boolean),required_experience:Number(form.required_experience)});toast('Job created!','success');setForm({title:'',company_name:'',location:'',required_skills:'',required_experience:0,salary_range:'',description:'',status:'open'})}catch(e){toast(e.response?.data?.detail||'Failed to create job','error')}}
  return <section><h1>Create Job</h1><form onSubmit={submit} className="form-grid">{['title','company_name','location','required_skills','required_experience','salary_range'].map(k=><div key={k}><label>{k.replace(/_/g,' ')}</label><input placeholder={k} value={form[k]} onChange={e=>setForm({...form,[k]:e.target.value})} type={k==='required_experience'?'number':'text'}/></div>)}<div><label>Description</label><textarea rows={4} placeholder="Description" value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></div><button className="btn btn-primary" style={{justifyContent:'center',padding:14}}>Create Job</button></form></section>
}
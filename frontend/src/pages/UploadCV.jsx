import { useState } from 'react'
import api from '../api/axiosClient'
import { useToast } from '../context/ToastContext'
import { Upload, CheckCircle, XCircle } from 'lucide-react'

export default function UploadCV({multiple=false}) {
  const toast = useToast()
  const [selected,setSelected]=useState([]); const [files,setFiles]=useState([]); const [uploading,setUploading]=useState(false)
  async function poll(cv) {
    for (let i = 0; i < 20; i++) {
      const r = await api.get(`/api/cv-queue/status/${cv.id}`)
      const item = r.data
      setFiles(prev => prev.map(f => f.id === cv.id ? {...f, queue:item, extracted_data:item.cv?.extracted_data||f.extracted_data} : f))
      if (['done','failed'].includes(item.status)) return item
      await new Promise(resolve => setTimeout(resolve, 2000))
    }
  }
  async function submit(e){e.preventDefault();if(selected.length===0)return toast('Select a PDF/DOCX first','error');const fd=new FormData();selected.forEach(f=>fd.append(multiple?'files':'file',f));setUploading(true);setFiles([]);try{const r=await api.post(multiple?'/api/cvs/upload-multiple':'/api/cvs/upload',fd);const rows=Array.isArray(r.data)?r.data:[r.data];toast(`Queued ${rows.length} CV${rows.length>1?'s':''} for processing`,'success');setFiles(rows.map(row=>({...row,queue:{status:'pending'}})));setSelected([]);rows.forEach(poll)}catch(e){toast(e.response?.data?.detail||'Upload failed','error')}finally{setUploading(false)}}
  return <section><h1>{multiple?'Upload Candidate CVs':'Upload CV'}</h1><form onSubmit={submit}><label className="upload-zone" htmlFor="fileInput" style={{cursor:'pointer'}}><Upload size={32}/><p>Drop your {multiple?'files':'file'} here or <span className="highlight">browse</span></p><p style={{marginTop:8,fontSize:'0.8rem'}}>Supports PDF and DOCX</p></label><input name="files" type="file" accept=".pdf,.docx" multiple={multiple} style={{display:'none'}} id="fileInput" onChange={e=>setSelected([...e.target.files])}/>{selected.length>0&&<div style={{marginTop:12}}>{selected.map(f=><div key={f.name} className="file-item"><Upload size={18}/><span className="filename">{f.name}</span><span className="status">Ready</span></div>)}</div>}<button type="button" className="btn btn-secondary" onClick={()=>document.getElementById('fileInput').click()} style={{marginTop:8}}>Select {multiple?'files':'file'}</button><button className="btn btn-primary" disabled={uploading||selected.length===0} style={{marginTop:8,marginLeft:8}}>{uploading?'Queueing...':'Upload to Queue'}</button></form>{files.length>0&&<div style={{marginTop:16}}><h3>Queue Results</h3>{files.map((f,i)=><div key={f.id||i} className="file-item">{f.queue?.status==='failed'?<XCircle size={18} color="var(--destructive)"/>:<CheckCircle size={18} color="var(--accent)"/>}<span className="filename">{f.filename||'CV #'+(i+1)}</span><span className="status">{f.queue?.status||f.processing_status||'queued'} · {(f.extracted_data?.skills||[]).slice(0,3).join(', ')||'extracting skills...'}</span></div>)}</div>}</section>
}

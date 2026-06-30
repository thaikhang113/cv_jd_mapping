import { useState } from 'react'
import api from '../api/axiosClient'
import { useToast } from '../context/ToastContext'
import { Upload, CheckCircle, XCircle } from 'lucide-react'

export default function UploadCV({multiple=false}) {
  const toast = useToast()
  const [files,setFiles]=useState([]); const [uploading,setUploading]=useState(false)
  async function submit(e){e.preventDefault();const fd=new FormData();[...e.target.files.files].forEach(f=>fd.append(multiple?'files':'file',f));setUploading(true);setFiles([]);try{const r=await api.post(multiple?'/api/cvs/upload-multiple':'/api/cvs/upload',fd);const count=Array.isArray(r.data)?r.data.length:1;toast(`Uploaded ${count} CV${count>1?'s':''}!`,'success');setFiles(Array.isArray(r.data)?r.data:[r.data])}catch(e){toast(e.response?.data?.detail||'Upload failed','error')}finally{setUploading(false)}}
  return <section><h1>{multiple?'Upload Candidate CVs':'Upload CV'}</h1><form onSubmit={submit}><div className="upload-zone"><Upload size={32}/><p>Drop your {multiple?'files':'file'} here or <span className="highlight">browse</span></p><p style={{marginTop:8,fontSize:'0.8rem'}}>Supports PDF and DOCX</p></div><input name="files" type="file" accept=".pdf,.docx" multiple={multiple} style={{display:'none'}} id="fileInput"/><button type="button" className="btn btn-secondary" onClick={()=>document.getElementById('fileInput').click()} style={{marginTop:8}}>Select {multiple?'files':'file'}</button>{uploading&&<p style={{marginTop:8,color:'var(--primary)',fontWeight:500}}>Uploading...</p>}</form>{files.length>0&&<div style={{marginTop:16}}><h3>Uploaded Files</h3>{files.map((f,i)=><div key={i} className="file-item"><CheckCircle size={18} color="var(--accent)"/><span className="filename">{f.filename||'CV #'+(i+1)}</span><span className="status">{(f.extracted_data?.skills||[]).slice(0,3).join(', ')}</span></div>)}</div>}</section>
}
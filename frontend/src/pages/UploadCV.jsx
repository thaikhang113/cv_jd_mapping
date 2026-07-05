import { useState } from 'react'
import api from '../api/axiosClient'
import { useToast } from '../context/ToastContext'
import { Upload, CheckCircle, Clock, XCircle } from 'lucide-react'

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))
const stageText = {
  ready: 'Ready',
  uploading: 'Uploading file',
  parsing: 'Parsing CV',
  pending: 'Waiting in matching queue',
  processing: 'Matching with jobs',
  done: 'Done',
  failed: 'Failed',
  timeout: 'Still processing',
}
function progressFor(status, uploadProgress = 0) {
  if (status === 'ready') return 0
  if (status === 'uploading') return Math.min(35, Math.max(5, Math.round(uploadProgress)))
  if (status === 'parsing') return 55
  if (status === 'pending') return 72
  if (status === 'processing') return 88
  if (status === 'done' || status === 'failed') return 100
  if (status === 'timeout') return 92
  return 10
}
function rowStatus(row) {
  return row.queue?.status || row.processing_status || row.status || 'ready'
}
function ProgressIcon({ status }) {
  if (status === 'failed') return <XCircle size={18} color="var(--destructive)" />
  if (status === 'done') return <CheckCircle size={18} color="var(--accent)" />
  return <Clock size={18} color="var(--primary)" />
}
function ProgressBar({ value, status }) {
  const cls = status === 'failed' ? 'failed' : status === 'done' ? 'complete' : 'active'
  return <div className="upload-progress"><div className="upload-progress-meta"><span>{stageText[status] || status}</span><b>{value}%</b></div><div className="progress-track"><div className={`progress-fill ${cls}`} style={{ width: `${value}%` }} /></div></div>
}

export default function UploadCV({ multiple=false }) {
  const toast = useToast()
  const [selected, setSelected] = useState([])
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)

  function updateRow(id, patch) {
    setFiles(prev => prev.map(row => row.localId === id || row.id === id ? { ...row, ...patch } : row))
  }

  async function poll(cv) {
    const id = cv.id
    for (let i = 0; i < 30; i++) {
      try {
        const r = await api.get(`/api/cv-queue/status/${id}`)
        const item = r.data
        const status = item.status || 'processing'
        updateRow(id, {
          queue: item,
          status,
          progress: progressFor(status),
          extracted_data: item.cv?.extracted_data || cv.extracted_data,
          processing_error: item.error || item.cv?.processing_error,
        })
        if (['done', 'failed'].includes(status)) return item
      } catch (e) {
        updateRow(id, { status: 'failed', progress: 100, processing_error: e.response?.data?.detail || 'Cannot read queue status' })
        return null
      }
      await sleep(2000)
    }
    updateRow(id, { status: 'timeout', progress: 92 })
    return null
  }

  async function submit(e) {
    e.preventDefault()
    if (selected.length === 0) return toast('Select a PDF/DOCX first', 'error')
    const pendingRows = selected.map((file, index) => ({ localId: `${file.name}-${index}-${Date.now()}`, filename: file.name, status: 'uploading', progress: 5, extracted_data: {} }))
    const fd = new FormData()
    selected.forEach(file => fd.append(multiple ? 'files' : 'file', file))
    setUploading(true)
    setFiles(pendingRows)
    try {
      const r = await api.post(multiple ? '/api/cvs/upload-multiple' : '/api/cvs/upload', fd, {
        onUploadProgress: event => {
          const total = event.total || selected.reduce((sum, file) => sum + file.size, 0) || 1
          const value = Math.min(35, Math.round((event.loaded / total) * 35))
          setFiles(prev => prev.map(row => ({ ...row, status: 'uploading', progress: Math.max(row.progress || 0, value) })))
        },
      })
      const rows = (Array.isArray(r.data) ? r.data : [r.data]).map((row, index) => {
        const failed = row.processing_status === 'failed'
        return {
          ...row,
          localId: pendingRows[index]?.localId || row.id,
          status: failed ? 'failed' : 'pending',
          progress: failed ? 100 : 72,
          queue: failed ? { status: 'failed', error: row.processing_error } : { status: 'pending' },
        }
      })
      toast(`Queued ${rows.length} CV${rows.length > 1 ? 's' : ''} for matching`, 'success')
      setFiles(rows)
      setSelected([])
      for (const row of rows) if (row.processing_status !== 'failed') poll(row)
    } catch (e) {
      const message = e.response?.data?.detail || 'Upload failed'
      setFiles(prev => prev.map(row => ({ ...row, status: 'failed', progress: 100, processing_error: message })))
      toast(message, 'error')
    } finally {
      setUploading(false)
    }
  }

  return <section><h1>{multiple ? 'Upload Candidate CVs' : 'Upload CV'}</h1><form onSubmit={submit}><label className="upload-zone" htmlFor="fileInput" style={{cursor:'pointer'}}><Upload size={32}/><p>Drop your {multiple ? 'files' : 'file'} here or <span className="highlight">browse</span></p><p style={{marginTop:8,fontSize:'0.8rem'}}>Supports PDF and DOCX</p></label><input name="files" type="file" accept=".pdf,.docx" multiple={multiple} style={{display:'none'}} id="fileInput" onChange={e=>setSelected([...e.target.files])}/>{selected.length>0&&<div style={{marginTop:12}}>{selected.map(f=><div key={f.name} className="file-item"><Upload size={18}/><span className="filename">{f.name}</span><span className="status">Ready</span></div>)}</div>}<button type="button" className="btn btn-secondary" onClick={()=>document.getElementById('fileInput').click()} style={{marginTop:8}}>Select {multiple ? 'files' : 'file'}</button><button type="submit" className="btn btn-primary" disabled={uploading||selected.length===0} style={{marginTop:8,marginLeft:8}}>{uploading ? 'Queueing...' : 'Upload to Queue'}</button></form>{files.length>0&&<div style={{marginTop:16}}><h3>Queue Progress</h3>{files.map((f,i)=>{const status=rowStatus(f);const progress=f.progress ?? progressFor(status);return <div key={f.id||f.localId||i} className="file-item file-progress-item"><ProgressIcon status={status}/><div className="file-progress-main"><div className="file-progress-head"><span className="filename">{f.filename||'CV #'+(i+1)}</span><span className="status">{status} · {(f.extracted_data?.skills||[]).slice(0,3).join(', ')||f.processing_error||'working...'}</span></div><ProgressBar value={progress} status={status}/></div></div>})}</div>}</section>
}

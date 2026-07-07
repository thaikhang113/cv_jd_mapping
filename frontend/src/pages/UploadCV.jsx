import { useState } from 'react'
import api from '../api/axiosClient'
import { useToast } from '../context/ToastContext'
import { Upload, CheckCircle, Clock, XCircle } from 'lucide-react'

const MAX_CV_FILE_BYTES = 10 * 1024 * 1024
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))
const stageText = {
  ready: 'Ready',
  uploading: 'Uploading file',
  queued: 'Queued',
  parsing: 'Parsing CV',
  pending: 'Queued',
  processing: 'Matching with jobs',
  done: 'Done',
  failed: 'Failed',
  timeout: 'Still processing',
}
function progressFor(status, uploadProgress = 0) {
  if (status === 'ready') return 0
  if (status === 'uploading') return Math.min(35, Math.max(5, Math.round(uploadProgress)))
  if (status === 'queued' || status === 'pending') return 72
  if (status === 'parsing') return 55
  if (status === 'processing') return 88
  if (status === 'done' || status === 'failed') return 100
  if (status === 'timeout') return 92
  return 10
}
function rowStatus(row) { return row.status || row.queue?.status || row.processing_status || 'ready' }
function isUploadSettled(row) { return row.upload_done || ['queued','pending','processing','done','failed','timeout'].includes(rowStatus(row)) }
function isMatchSettled(row) { return ['done','failed','timeout'].includes(rowStatus(row)) }
function percent(done, total) { return total ? Math.round((done / total) * 100) : 0 }
function fileLimitMessage() { return 'File exceeds 10 MB limit' }
function ProgressIcon({ status }) {
  if (status === 'failed' || status === 'timeout') return <XCircle size={18} color="var(--destructive)" />
  if (status === 'done') return <CheckCircle size={18} color="var(--accent)" />
  return <Clock size={18} color="var(--primary)" />
}
function ProgressBar({ value, status, label }) {
  const cls = status === 'failed' || status === 'timeout' ? 'failed' : status === 'done' ? 'complete' : 'active'
  return <div className="upload-progress"><div className="upload-progress-meta"><span>{label || stageText[status] || status}</span><b>{value}%</b></div><div className="progress-track"><div className={`progress-fill ${cls}`} style={{ width: `${value}%` }} /></div></div>
}

export default function UploadCV({ multiple=false }) {
  const toast = useToast()
  const [selected, setSelected] = useState([])
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)

  function updateRow(id, patch) {
    setFiles(prev => prev.map(row => row.localId === id || row.id === id ? { ...row, ...patch } : row))
  }

  async function poll(row) {
    const id = row.id
    for (let i = 0; i < 30; i++) {
      try {
        const r = await api.get(`/api/cv-queue/status/${id}`)
        const item = r.data
        const status = item.status || 'processing'
        updateRow(id, {
          queue: item,
          status,
          progress: progressFor(status),
          extracted_data: item.cv?.extracted_data || row.extracted_data,
          processing_error: item.error || item.cv?.processing_error,
        })
        if (['done', 'failed'].includes(status)) return item
      } catch (e) {
        updateRow(id, { status: 'failed', progress: 100, upload_done: true, processing_error: e.response?.data?.detail || 'Cannot read queue status' })
        return null
      }
      await sleep(2000)
    }
    updateRow(id, { status: 'timeout', progress: 92, upload_done: true, processing_error: 'Matching timeout' })
    return null
  }

  async function uploadOne(row, file) {
    if (file.size > MAX_CV_FILE_BYTES) {
      updateRow(row.localId, { status: 'failed', progress: 100, upload_done: true, processing_error: fileLimitMessage() })
      return null
    }
    const fd = new FormData()
    fd.append('file', file)
    try {
      const r = await api.post('/api/cvs/upload', fd, {
        onUploadProgress: event => {
          const total = event.total || file.size || 1
          const value = Math.min(35, Math.round((event.loaded / total) * 35))
          updateRow(row.localId, { status: 'uploading', progress: value })
        },
      })
      const failed = r.data.processing_status === 'failed'
      const next = {
        ...r.data,
        localId: row.localId,
        upload_done: true,
        status: failed ? 'failed' : 'queued',
        progress: failed ? 100 : 72,
        queue: failed ? { status: 'failed', error: r.data.processing_error } : { status: 'queued' },
      }
      updateRow(row.localId, next)
      if (!failed) poll(next)
      return next
    } catch (e) {
      updateRow(row.localId, { status: 'failed', progress: 100, upload_done: true, processing_error: e.response?.data?.detail || 'Upload failed' })
      return null
    }
  }

  async function submit(e) {
    e.preventDefault()
    if (selected.length === 0) return toast('Select a PDF/DOCX first', 'error')
    const startedAt = Date.now()
    const pendingRows = selected.map((file, index) => ({ localId: `${file.name}-${index}-${startedAt}`, filename: file.name, status: 'ready', progress: 0, extracted_data: {}, upload_done: false }))
    setUploading(true)
    setFiles(pendingRows)
    let queued = 0
    for (let i = 0; i < selected.length; i++) {
      updateRow(pendingRows[i].localId, { status: 'uploading', progress: 5 })
      const row = await uploadOne(pendingRows[i], selected[i])
      if (row && row.status !== 'failed') queued += 1
    }
    toast(`Queued ${queued}/${selected.length} CV${selected.length > 1 ? 's' : ''} for matching`, queued ? 'success' : 'error')
    setSelected([])
    setUploading(false)
  }

  const total = files.length
  const uploaded = files.filter(isUploadSettled).length
  const matched = files.filter(isMatchSettled).length

  return <section><h1>{multiple ? 'Upload Candidate CVs' : 'Upload CV'}</h1><form onSubmit={submit}><label className="upload-zone" htmlFor="fileInput" style={{cursor:'pointer'}}><Upload size={32}/><p>Drop your {multiple ? 'files' : 'file'} here or <span className="highlight">browse</span></p><p style={{marginTop:8,fontSize:'0.8rem'}}>Supports PDF and DOCX. Max 10 MB per CV.</p></label><input name="files" type="file" accept=".pdf,.docx" multiple={multiple} style={{display:'none'}} id="fileInput" onChange={e=>setSelected([...e.target.files])}/>{selected.length>0&&<div style={{marginTop:12}}>{selected.map(f=><div key={f.name} className="file-item"><Upload size={18}/><span className="filename">{f.name}</span><span className={f.size > MAX_CV_FILE_BYTES ? 'status err' : 'status'}>{f.size > MAX_CV_FILE_BYTES ? fileLimitMessage() : 'Ready'}</span></div>)}</div>}<button type="button" className="btn btn-secondary" onClick={()=>document.getElementById('fileInput').click()} style={{marginTop:8}}>Select {multiple ? 'files' : 'file'}</button><button type="submit" className="btn btn-primary" disabled={uploading||selected.length===0} style={{marginTop:8,marginLeft:8}}>{uploading ? 'Queueing...' : 'Upload to Queue'}</button></form>{files.length>0&&<div style={{marginTop:16}}><h3>Queue Progress</h3><div className="batch-progress-grid"><ProgressBar value={percent(uploaded,total)} status={uploaded===total?'done':'processing'} label={`Upload/Queue: ${uploaded}/${total}`} /><ProgressBar value={percent(matched,total)} status={matched===total?'done':'processing'} label={`Matching: ${matched}/${total}`} /></div>{files.map((f,i)=>{const status=rowStatus(f);const progress=f.progress ?? progressFor(status);return <div key={f.id||f.localId||i} className="file-item file-progress-item"><ProgressIcon status={status}/><div className="file-progress-main"><div className="file-progress-head"><span className="filename">{f.filename||'CV #'+(i+1)}</span><span className="status">{stageText[status] || status} - {(f.extracted_data?.skills||[]).slice(0,3).join(', ')||f.processing_error||'working...'}</span></div><ProgressBar value={progress} status={status}/></div></div>})}</div>}</section>
}

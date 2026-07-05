import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api/axiosClient'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function JobDetail() {
  const { jobId } = useParams()
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)

  useEffect(() => {
    api.get(`/api/jobs/${jobId}`).then(r => setJob(r.data)).catch(() => toast('Job not found', 'error')).finally(() => setLoading(false))
  }, [jobId, toast])

  async function apply() {
    setApplying(true)
    try {
      await api.post('/api/applications', { job_id: jobId })
      toast('Applied successfully', 'success')
      navigate('/candidate/applications')
    } catch (e) {
      toast(e.response?.data?.detail || 'Apply failed', 'error')
    } finally {
      setApplying(false)
    }
  }

  if (loading) return <section><h1>Loading job...</h1></section>
  if (!job) return <section><h1>Job not found</h1><Link className="btn" to="/candidate/jobs">Back to jobs</Link></section>

  return <section className="detail-page">
    <div className="page-head"><div><p className="eyebrow">Job detail</p><h1>{job.title}</h1><p className="muted">{job.company_name} · {job.location}</p></div><span className="badge">{job.status}</span></div>
    <div className="grid two"><div className="card"><h2>Requirements</h2><p><b>Skills:</b> {(job.required_skills || []).join(', ') || 'Not specified'}</p><p><b>Experience:</b> {job.required_experience || 0}+ years</p><p><b>Salary:</b> {job.salary_range || 'Negotiable'}</p></div><div className="card"><h2>Description</h2><p style={{ whiteSpace: 'pre-wrap' }}>{job.description}</p></div></div>
    {user?.role === 'candidate' && <button className="btn btn-primary" disabled={applying || job.status !== 'open'} onClick={apply}>{applying ? 'Applying...' : 'Apply now'}</button>}
    {user?.role === 'recruiter' && <Link className="btn btn-primary" to="/recruiter/ranking">View ranking</Link>}
  </section>
}

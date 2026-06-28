import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
export default function Applications() { const [rows,setRows]=useState([]); useEffect(()=>{api.get('/api/applications/my').then(r=>setRows(r.data))},[]); return <section><h1>Applications Management</h1><table><tbody>{rows.map(a=><tr key={a.id}><td>{a.job_id}</td><td>{a.candidate_id}</td><td>{a.status}</td></tr>)}</tbody></table></section> }

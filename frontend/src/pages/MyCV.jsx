import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
export default function MyCV() { const [rows,setRows]=useState([]); useEffect(()=>{api.get('/api/cvs/my').then(r=>setRows(r.data))},[]); return <section><h1>My CV Profile</h1>{rows.map(cv=><div className="card" key={cv.id}><h3>{cv.filename}</h3><p>{cv.extracted_data?.email} · {cv.extracted_data?.phone}</p><p>{(cv.extracted_data?.skills||[]).join(', ')}</p></div>)}</section> }

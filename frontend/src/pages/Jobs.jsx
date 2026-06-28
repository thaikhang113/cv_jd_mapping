import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
export default function Jobs({ mine=false }) { const [rows,setRows]=useState([]); useEffect(()=>{api.get(mine?'/api/jobs/my':'/api/jobs').then(r=>setRows(r.data))},[mine]); return <section><h1>{mine?'My Jobs':'Matching Jobs'}</h1><table><tbody>{rows.map(j=><tr key={j.id}><td><b>{j.title}</b><br/>{j.company_name}</td><td>{j.location}</td><td>{(j.required_skills||[]).join(', ')}</td></tr>)}</tbody></table></section> }

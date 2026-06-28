import { useEffect, useState } from 'react'
import api from '../api/axiosClient'
export default function AdminTable({ type }) { const [rows,setRows]=useState([]); useEffect(()=>{api.get(`/api/admin/${type}`).then(r=>setRows(r.data))},[type]); return <section><h1>Manage {type}</h1><table><tbody>{rows.map(row=><tr key={row.id}>{Object.entries(row).slice(0,6).map(([k,v])=><td key={k}><small>{k}</small><br/>{Array.isArray(v)?v.join(', '):String(v ?? '')}</td>)}</tr>)}</tbody></table></section> }

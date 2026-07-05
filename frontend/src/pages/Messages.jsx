import { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../api/axiosClient'
import { MessageSquare } from 'lucide-react'

export default function Messages() {
  const [params] = useSearchParams()
  const [convos,setConvos]=useState([]); const [active,setActive]=useState(null); const [msgs,setMsgs]=useState([]); const [text,setText]=useState('')
  const boxRef = useRef(null)
  useEffect(()=>{api.get('/api/conversations/my').then(r=>setConvos(r.data))},[])
  useEffect(()=>{const id=params.get('conversation'); if(!id)return; const found=convos.find(x=>x.id===id); if(found) open(found); else api.get('/api/conversations/'+id).then(r=>{setConvos(prev=>prev.some(c=>c.id===r.data.id)?prev:[r.data,...prev]); open(r.data)}).catch(()=>{})},[params,convos])
  useEffect(()=>{if(boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight},[msgs])
  async function open(c){setActive(c);const d=(await api.get('/api/messages/'+c.id)).data;setMsgs(d)}
  async function send(){if(!active||!text.trim())return;await api.post('/api/messages',{conversation_id:active.id,content:text.trim()});setText('');const refreshed=(await api.get('/api/conversations/my')).data;setConvos(refreshed);open(active)}

  return <section><h1>Messages</h1><div className="chat"><div className="chat-sidebar">{convos.length===0 ? <div className="empty-state"><MessageSquare size={40} strokeWidth={1.5}/><p>No conversations</p></div> : convos.map(c => <div key={c.id} className={'chat-convo'+(active?.id===c.id?' active':'')} onClick={()=>open(c)}><div className="chat-convo-name">{c.other_name||'User'}</div><div className="chat-convo-preview">{c.last_message||'No messages'}</div></div>)}</div><div className="chat-main">{!active ? <div className="empty-state" style={{height:'100%'}}><MessageSquare size={48} strokeWidth={1.5}/><h3>Select a conversation</h3><p>Choose from the list to start chatting</p></div> : <><div className="chat-header">{active.other_name||'User'}</div><div className="chat-box" ref={boxRef}>{msgs.length===0 ? <div className="empty-state"><MessageSquare size={32}/><p>No messages yet</p></div> : msgs.map(m => <div key={m.id} className={'chat-bubble '+(m.is_me?'sent':'received')}><div className="chat-name">{m.sender_name||'User'}</div>{m.content}<div className="chat-time">{new Date(m.created_at).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</div></div>)}</div><div className="chat-input-wrap"><input placeholder="Type your message..." value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=>{if(e.key==='Enter')send()}}/><button onClick={send}>Send</button></div></>}</div></div></section>
}

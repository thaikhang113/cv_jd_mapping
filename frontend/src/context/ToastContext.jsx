import { createContext, useContext, useState, useCallback } from 'react'
const ToastCtx = createContext(null)
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const add = useCallback((msg, type = 'success') => {
    const id = Date.now()
    setToasts(p => [...p, { id, msg, type }])
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 3500)
  }, [])
  return (<ToastCtx.Provider value={add}>
    <div className="toast-container">
      {toasts.map(t => (<div key={t.id} className={'toast toast-' + t.type}>
        {t.type === 'success' ? <CheckIcon /> : <XIcon />}{t.msg}</div>))}
    </div>
  </ToastCtx.Provider>)
}
function CheckIcon() { return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg> }
function XIcon() { return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></svg> }
export const useToast = () => useContext(ToastCtx)
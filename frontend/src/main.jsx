import React, { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import Routes from './routes/Routes'
import './style.css'
createRoot(document.getElementById('root')).render(<StrictMode><ToastProvider><AuthProvider><Routes /></AuthProvider></ToastProvider></StrictMode>)
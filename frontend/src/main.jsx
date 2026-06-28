import React from 'react'
import { createRoot } from 'react-dom/client'
import { AuthProvider } from './context/AuthContext'
import Routes from './routes/Routes'
import './style.css'

createRoot(document.getElementById('root')).render(<React.StrictMode><AuthProvider><Routes /></AuthProvider></React.StrictMode>)

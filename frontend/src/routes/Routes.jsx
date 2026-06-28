import { Navigate, RouterProvider, createBrowserRouter } from 'react-router-dom'
import AppLayout from '../layouts/AppLayout'
import Login from '../pages/Login'
import Register from '../pages/Register'
import Dashboard from '../pages/Dashboard'
import UploadCV from '../pages/UploadCV'
import MyCV from '../pages/MyCV'
import Jobs from '../pages/Jobs'
import CreateJob from '../pages/CreateJob'
import Ranking from '../pages/Ranking'
import Applications from '../pages/Applications'
import Messages from '../pages/Messages'
import Profile from '../pages/Profile'
import AdminTable from '../pages/AdminTable'

const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/login" /> },
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },
  { element: <AppLayout />, children: [
    { path: '/candidate', element: <Dashboard role="candidate" /> },
    { path: '/candidate/upload-cv', element: <UploadCV /> },
    { path: '/candidate/cv', element: <MyCV /> },
    { path: '/candidate/jobs', element: <Jobs /> },
    { path: '/candidate/applications', element: <Applications /> },
    { path: '/recruiter', element: <Dashboard role="recruiter" /> },
    { path: '/recruiter/jobs/new', element: <CreateJob /> },
    { path: '/recruiter/jobs', element: <Jobs mine /> },
    { path: '/recruiter/upload-cvs', element: <UploadCV multiple /> },
    { path: '/recruiter/ranking', element: <Ranking /> },
    { path: '/recruiter/applications', element: <Applications /> },
    { path: '/admin', element: <Dashboard role="admin" /> },
    { path: '/admin/users', element: <AdminTable type="users" /> },
    { path: '/admin/cvs', element: <AdminTable type="cvs" /> },
    { path: '/admin/jobs', element: <AdminTable type="jobs" /> },
    { path: '/admin/matches', element: <AdminTable type="matches" /> },
    { path: '/admin/applications', element: <AdminTable type="applications" /> },
    { path: '/messages', element: <Messages /> },
    { path: '/profile', element: <Profile /> },
  ]}
])
export default function Routes(){ return <RouterProvider router={router} /> }

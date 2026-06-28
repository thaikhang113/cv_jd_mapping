import { useAuth } from '../context/AuthContext'
export default function Profile() { const { user } = useAuth(); return <section><h1>Profile</h1><div className="card"><p>{user?.name}</p><p>{user?.email}</p><p>{user?.role}</p></div></section> }

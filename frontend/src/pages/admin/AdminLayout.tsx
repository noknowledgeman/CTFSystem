import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export default function AdminLayout() {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()

  if (!user || !isAdmin) {
    return (
      <div className="app">
        <p className="error">Admin access required.</p>
        <button type="button" className="btn" onClick={() => navigate('/login')}>Go to login</button>
      </div>
    )
  }

  return (
    <div className="app">
      <nav className="nav">
        <NavLink to="/">Player view</NavLink>
        <NavLink to="/admin" end className={({ isActive }) => (isActive ? 'active' : '')}>Stats</NavLink>
        <NavLink to="/admin/challenges" className={({ isActive }) => (isActive ? 'active' : '')}>Challenges</NavLink>
        <NavLink to="/admin/users" className={({ isActive }) => (isActive ? 'active' : '')}>Users</NavLink>
        <NavLink to="/admin/submissions" className={({ isActive }) => (isActive ? 'active' : '')}>Submissions</NavLink>
        <NavLink to="/admin/vm" className={({ isActive }) => (isActive ? 'active' : '')}>VM config</NavLink>
        <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>{user.username}</span>
        <button type="button" className="btn" onClick={() => { logout(); navigate('/login'); }}>Logout</button>
      </nav>
      <Outlet />
    </div>
  )
}

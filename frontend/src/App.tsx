import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ChallengeDetail from './pages/ChallengeDetail'
import AdminLayout from './pages/admin/AdminLayout'
import AdminStats from './pages/admin/AdminStats'
import AdminChallenges from './pages/admin/AdminChallenges'
import AdminSubmissions from './pages/admin/AdminSubmissions'
import AdminVm from './pages/admin/AdminVm'
import AdminUsers from './pages/admin/AdminUsers'
import Teams from './pages/Teams'
import Progress from './pages/Progress'

function Nav() {
  const { user, loading, isAdmin, logout } = useAuth()
  const navigate = useNavigate()
  if (loading) return null
  return (
    <nav className="nav">
      <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>Dashboard</NavLink>
      <NavLink to="/teams" className={({ isActive }) => (isActive ? 'active' : '')}>Teams</NavLink>
      <NavLink to="/progress" className={({ isActive }) => (isActive ? 'active' : '')}>Progress</NavLink>
      {isAdmin && <NavLink to="/admin" className={({ isActive }) => (isActive ? 'active' : '')}>Admin</NavLink>}
      {user ? (
        <>
          <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>{user.username}</span>
          <button type="button" className="btn" onClick={() => { logout(); navigate('/login'); }}>Logout</button>
        </>
      ) : (
        <>
          <span style={{ marginLeft: 'auto' }} />
          <NavLink to="/login">Login</NavLink>
          <NavLink to="/register">Register</NavLink>
        </>
      )}
    </nav>
  )
}

function AppRoutes() {
  const { loading } = useAuth()
  if (loading) return <div className="app"><p>Loading…</p></div>

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<><Nav /><Dashboard /></>} />
      <Route path="/challenge/:id" element={<><Nav /><ChallengeDetail /></>} />
      <Route path="/teams" element={<><Nav /><Teams /></>} />
      <Route path="/progress" element={<><Nav /><Progress /></>} />
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<AdminStats />} />
        <Route path="challenges" element={<AdminChallenges />} />
        <Route path="users" element={<AdminUsers />} />
        <Route path="submissions" element={<AdminSubmissions />} />
        <Route path="vm" element={<AdminVm />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import type { User } from '../types'
import { auth as authApi } from '../api/client'

const TOKEN_KEY = 'ctf_token'
const USER_KEY = 'ctf_user'

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<User>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  updateUser: (user: User) => void
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem(TOKEN_KEY),
    loading: true,
  })

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    const raw = localStorage.getItem(USER_KEY)
    if (token && raw) {
      try {
        const user = JSON.parse(raw) as User
        setState({ user, token, loading: false })
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setState((s) => ({ ...s, user: null, token: null, loading: false }))
      }
    } else {
      setState((s) => ({ ...s, loading: false }))
    }
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const res = await authApi.login(username, password)
    localStorage.setItem(TOKEN_KEY, res.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(res.user))
    setState({ user: res.user, token: res.access_token, loading: false })
    return res.user
  }, [])

  const register = useCallback(async (username: string, email: string, password: string) => {
    const res = await authApi.register(username, email, password)
    localStorage.setItem(TOKEN_KEY, res.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(res.user))
    setState({ user: res.user, token: res.access_token, loading: false })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setState({ user: null, token: null, loading: false })
  }, [])

  const updateUser = useCallback((user: User) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    setState((s) => (s.token ? { ...s, user } : s))
  }, [])

  const value: AuthContextValue = {
    ...state,
    login,
    register,
    logout,
    updateUser,
    isAdmin: state.user?.role === 'admin',
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

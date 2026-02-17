import type { Challenge, Hint, Submission, LeaderboardEntry, EventStats, TokenResponse, User, ProgressDetailed } from '../types'

const API_BASE = '/api'

function getToken(): string | null {
  return localStorage.getItem('ctf_token')
}

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || JSON.stringify(err))
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// Auth
export const auth = {
  login: (username: string, password: string) =>
    api<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  register: (username: string, email: string, password: string) =>
    api<TokenResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    }),
}

// Challenges
export const challenges = {
  list: () => api<Challenge[]>('/challenges'),
  get: (id: number) => api<Challenge>(`/challenges/${id}`),
  create: (data: Record<string, unknown>) =>
    api<Challenge>('/challenges', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Record<string, unknown>) =>
    api<Challenge>(`/challenges/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) =>
    api<void>(`/challenges/${id}`, { method: 'DELETE' }),
}

// Hints
export const hints = {
  list: (challengeId: number) =>
    api<Hint[]>(`/hints/challenge/${challengeId}`),
  unlockNext: (challengeId: number) =>
    api<Hint>(`/hints/challenge/${challengeId}/unlock`, { method: 'POST' }),
  create: (data: { challenge_id: number; order: number; content: string; cost?: number }) =>
    api<Hint>('/hints', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Record<string, unknown>) =>
    api<Hint>(`/hints/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: number) =>
    api<void>(`/hints/${id}`, { method: 'DELETE' }),
}

// Submissions
export const submissions = {
  submit: (challenge_id: number, flag: string, description?: string) =>
    api<Submission>('/submissions', {
      method: 'POST',
      body: JSON.stringify({ challenge_id, flag, description }),
    }),
  my: () => api<Submission[]>('/submissions'),
  all: (params?: { challenge_id?: number; user_id?: number; team_id?: number }) => {
    const sp = new URLSearchParams()
    if (params?.challenge_id != null) sp.set('challenge_id', String(params.challenge_id))
    if (params?.user_id != null) sp.set('user_id', String(params.user_id))
    if (params?.team_id != null) sp.set('team_id', String(params.team_id))
    const q = sp.toString()
    return api<Submission[]>(`/submissions/all${q ? `?${q}` : ''}`)
  },
  grade: (id: number, data: { status: string; assigned_points?: number; feedback?: string }) =>
    api<Submission>(`/submissions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
}

// Leaderboard
export const leaderboard = {
  get: (by: 'user' | 'team' = 'user') =>
    api<LeaderboardEntry[]>(`/leaderboard?by=${by}`),
  myProgress: () =>
    api<{ total_points: number; solved_count: number; username: string }>('/leaderboard/me'),
  myProgressDetailed: () =>
    api<ProgressDetailed>('/leaderboard/me/detailed'),
}

// Teams (player)
export const teams = {
  list: () => api<TeamRead[]>('/teams'),
  join: (teamId: number) => api<{ team: TeamRead; user: User }>(`/teams/${teamId}/join`, { method: 'POST' }),
  leave: () => api<{ user: User }>('/teams/leave', { method: 'POST' }),
}

// Admin
export const admin = {
  users: () => api<User[]>('/admin/users'),
  updateUser: (userId: number, data: { is_active?: boolean }) =>
    api<User>(`/admin/users/${userId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  getChallengeHints: (challengeId: number) =>
    api<Hint[]>(`/admin/challenges/${challengeId}/hints`),
  teams: () => api<TeamRead[]>('/admin/teams'),
  createTeam: (name: string) =>
    api<TeamRead>('/admin/teams', { method: 'POST', body: JSON.stringify({ name }) }),
  stats: () => api<EventStats>('/admin/stats'),
  uploadVmConfig: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${API_BASE}/admin/vm-config`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` },
      body: form,
    }).then((r) => (r.ok ? r.json() : r.json().then((e) => Promise.reject(new Error(e.detail)))))
  },
}

export interface TeamRead {
  id: number
  name: string
  created_at: string
}

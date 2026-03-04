import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '../contexts/AuthContext'
import * as api from '../api/client'
import Teams from '../pages/Teams'
import type { LeaderboardEntry } from '../types'

// Helper wrapper to control auth state
function AuthWrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}

vi.mock('../contexts/AuthContext', async () => {
  const actual = await vi.importActual<typeof import('../contexts/AuthContext')>('../contexts/AuthContext')
  return {
    ...actual,
    useAuth: vi.fn(),
  }
})

describe('Teams page', () => {
  it('shows a message when user is not logged in', () => {
    ;(useAuth as unknown as vi.Mock).mockReturnValue({ user: null })
    render(
      <AuthWrapper>
        <Teams />
      </AuthWrapper>,
    )
    expect(screen.getByText(/Log in to view and join teams./i)).toBeInTheDocument()
  })

  it('renders teams and leaderboard when user is logged in', async () => {
    ;(useAuth as unknown as vi.Mock).mockReturnValue({
      user: { id: 1, username: 'alice', email: 'a@example.com', role: 'player', team_id: null, created_at: '', is_active: true },
      updateUser: vi.fn(),
    })

    vi.spyOn(api.teams, 'list').mockResolvedValue([
      { id: 1, name: 'Alpha', created_at: '2026-03-04T13:00:00Z' },
    ])
    const lb: LeaderboardEntry[] = [
      { rank: 1, user_id: null, team_id: 1, username_or_team: 'Alpha', total_points: 100, solved_count: 2 },
    ]
    vi.spyOn(api.leaderboard, 'get').mockResolvedValue(lb)

    render(
      <AuthWrapper>
        <Teams />
      </AuthWrapper>,
    )

    await waitFor(() => {
      expect(screen.getByText('Teams')).toBeInTheDocument()
      expect(screen.getByText('Alpha')).toBeInTheDocument()
    })
  })
})


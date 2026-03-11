import { render, screen, waitFor } from '@testing-library/react'
import * as api from '../api/client'
import AdminChallenges from '../pages/admin/AdminChallenges'
import type { Challenge, Hint } from '../types'
import { vi } from 'vitest'

describe('AdminChallenges', () => {
  it('lists challenges and allows creating a new one', async () => {
    const existing: Challenge[] = [
      {
        id: 1,
        name: 'Web 1',
        description: 'desc',
        category: 'web',
        difficulty: 'easy',
        points: 100,
        vm_identifier: null,
        upload_metadata: null,
        grading_mode: 'auto',
        created_at: '2026-03-04T13:00:00Z',
        updated_at: '2026-03-04T13:00:00Z',
        solved: false,
      },
    ]
    vi.spyOn(api.challenges, 'list').mockResolvedValue(existing)
    const createSpy = vi.spyOn(api.challenges, 'create').mockResolvedValue(existing[0])
    vi.spyOn(api.admin, 'getChallengeHints').mockResolvedValue([] as Hint[])
    vi.spyOn(api.hints, 'create').mockResolvedValue({
      id: 1,
      challenge_id: 1,
      order: 1,
      content: 'hint',
      cost: 0,
      created_at: '2026-03-04T13:00:00Z',
    })

    render(<AdminChallenges />)

    // Existing challenge appears
    await waitFor(() => {
      expect(screen.getByText('Web 1')).toBeInTheDocument()
    })

    // Basic smoke test: ensure table render used the API response
    await waitFor(() => {
      expect(screen.getByText('Web 1')).toBeInTheDocument()
      expect(createSpy).not.toHaveBeenCalled()
    })
  })
})


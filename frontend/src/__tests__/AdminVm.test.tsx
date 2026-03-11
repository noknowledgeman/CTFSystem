import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import * as api from '../api/client'
import AdminVm from '../pages/admin/AdminVm'
import { vi } from 'vitest'

describe('AdminVm', () => {
  it('renders headings and triggers validation', async () => {
    const validateSpy = vi.spyOn(api.admin, 'validateChallenges').mockResolvedValue([
      {
        challenge_id: 1,
        name: 'Web 1',
        vm_identifier: 'team1-vm',
        status: 'ok',
        error: null,
        checked_at: '2026-03-04T13:00:00Z',
      },
    ])
    vi.spyOn(api.admin, 'uploadVmConfig').mockResolvedValue({
      filename: 'vm.json',
      size: 123,
      message: 'ok',
    })

    render(<AdminVm />)

    expect(screen.getByText(/VM config & validation/i)).toBeInTheDocument()
    expect(screen.getByText(/Upload VM config/i)).toBeInTheDocument()

    const button = screen.getByRole('button', { name: /Run validation/i })
    fireEvent.click(button)

    await waitFor(() => {
      expect(validateSpy).toHaveBeenCalledTimes(1)
      expect(screen.getByText('Web 1')).toBeInTheDocument()
      expect(screen.getByText('team1-vm')).toBeInTheDocument()
      expect(screen.getByText('ok')).toBeInTheDocument()
    })
  })
})


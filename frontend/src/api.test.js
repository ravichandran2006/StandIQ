import { afterEach, describe, expect, it, vi } from 'vitest'
import { getHealth } from './api'

afterEach(() => vi.restoreAllMocks())

describe('health API boundary', () => {
  it('returns the backend health payload', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'healthy' }) }))

    await expect(getHealth()).resolves.toEqual({ status: 'healthy' })
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/health')
  })

  it('raises when the backend rejects the request', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }))

    await expect(getHealth()).rejects.toThrow('Health request failed with status 503')
  })
})

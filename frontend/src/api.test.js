import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  analyzeRequirement,
  fetchExplanation,
  fetchRelatedStandards,
  fetchTenderSpecification,
  getHealth,
  languageLabel,
  refineRequirement,
  uploadDocument,
} from './api'

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

describe('recommendation API boundary', () => {
  it('posts the requirement and returns structured recommendations', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ standards: [] }) }))

    await expect(analyzeRequirement('industrial cable tray')).resolves.toEqual({ standards: [] })
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'industrial cable tray' }),
    })
  })

  it('surfaces structured backend errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({ error: { message: 'Database is unavailable' } }) }))

    await expect(analyzeRequirement('industrial cable tray')).rejects.toThrow('Database is unavailable')
  })

  it('calls refine, explanation, related, and tender endpoints', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'success' }) }))

    await refineRequirement('steel', 'outdoor structural use')
    await fetchExplanation('steel', 'std-1')
    await fetchRelatedStandards('std-1')
    await fetchTenderSpecification('steel')

    expect(fetch).toHaveBeenCalledTimes(4)
  })

  it('posts uploaded document as multipart/form-data to /api/v1/recommendations/upload', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ requirement: { original_text: 'sample' }, standards: [] }) }))
    const dummyFile = new Blob(['dummy pdf'], { type: 'application/pdf' })
    dummyFile.name = 'test.pdf'

    const res = await uploadDocument(dummyFile)
    expect(res.requirement.original_text).toBe('sample')
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/recommendations/upload', expect.objectContaining({
      method: 'POST',
      body: expect.any(FormData),
    }))
  })

  it('surfaces backend errors for upload failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ error: { message: 'Unable to extract text from the uploaded PDF.' }, detail: 'Unable to extract text from the uploaded PDF.' })
    }))
    const dummyFile = new Blob(['corrupt'], { type: 'application/pdf' })
    dummyFile.name = 'corrupt.pdf'

    await expect(uploadDocument(dummyFile)).rejects.toThrow('Unable to extract text from the uploaded PDF.')
  })
})

describe('language labels', () => {
  it('maps supported language codes to native labels', () => {
    expect(languageLabel('hi')).toBe('हिन्दी')
    expect(languageLabel('ta')).toBe('தமிழ்')
    expect(languageLabel('ml')).toBe('മലയാളം')
    expect(languageLabel('en')).toBe('English')
  })
})

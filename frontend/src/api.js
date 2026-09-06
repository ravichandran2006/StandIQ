const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${apiBaseUrl}${path}`, options)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body?.error?.message || body?.detail || `Request failed with status ${response.status}`)
  }
  return body
}

export async function getHealth() {
  const response = await fetch(`${apiBaseUrl}/api/v1/health`)
  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`)
  }
  return response.json()
}

export async function analyzeRequirement(text, language) {
  return request('/api/v1/recommendations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, ...(language ? { language } : {}) }),
  })
}

export async function uploadDocument(file, language) {
  const formData = new FormData()
  formData.append('file', file)
  if (language) {
    formData.append('language', language)
  }
  const response = await fetch(`${apiBaseUrl}/api/v1/recommendations/upload`, {
    method: 'POST',
    body: formData,
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body?.error?.message || body?.detail || `Request failed with status ${response.status}`)
  }
  return body
}

export async function refineRequirement(originalText, refinement, language) {
  return request('/api/v1/recommendations/refine', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ original_text: originalText, refinement, ...(language ? { language } : {}) }),
  })
}

export async function fetchExplanation(text, standardId, language) {
  return request('/api/v1/recommendations/explanation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, standard_id: standardId, ...(language ? { language } : {}) }),
  })
}

export async function fetchTenderSpecification(text, language) {
  return request('/api/v1/recommendations/tender', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, ...(language ? { language } : {}) }),
  })
}

export async function fetchRelatedStandards(standardId) {
  return request(`/api/v1/recommendations/standards/${standardId}/related`)
}

export async function fetchVersionHistory(standardId) {
  return request(`/api/v1/recommendations/standards/${standardId}/version-history`)
}

export async function fetchComplianceDetails(standardId) {
  return request(`/api/v1/recommendations/standards/${standardId}/compliance`)
}

export async function fetchRequirementMapping(standardId, text) {
  return request(`/api/v1/recommendations/standards/${standardId}/mapping`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
}

export async function fetchSourceDocuments(standardId) {
  return request(`/api/v1/recommendations/standards/${standardId}/sources`)
}

export async function fetchAllEvidence(standardId, text) {
  return request(`/api/v1/recommendations/standards/${standardId}/evidence`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
}

export const LANGUAGE_LABELS = {
  en: 'English',
  hi: 'हिन्दी',
  ta: 'தமிழ்',
  ml: 'മലയാളം',
}

export function languageLabel(code) {
  return LANGUAGE_LABELS[code] || code
}

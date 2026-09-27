const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function getToken() {
  return localStorage.getItem('careerai_token')
}

export function setToken(token) {
  localStorage.setItem('careerai_token', token)
}

export function clearToken() {
  localStorage.removeItem('careerai_token')
}

export function accountStorageKey(key, userId) {
  return userId ? `careerai_${key}_${userId}` : `careerai_${key}`
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {})
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const message = data?.detail || data?.message || `Request failed (${response.status})`
    throw new Error(message)
  }
  return data
}

export const endpoints = {
  health: () => api('/health'),
  me: () => api('/auth/me'),
  recommendations: () => api('/recommendations/'),
  jobs: () => api('/jobs'),
  job: (id) => api(`/jobs/${id}`),
  applications: (query = '') => api(`/applications${query}`),
  application: (id) => api(`/applications/${id}`),
  applicationSummary: () => api('/applications/summary'),
  applicationLifecycle: () => api('/applications/lifecycle'),
  createApplication: (payload) => api('/applications', { method: 'POST', body: JSON.stringify(payload) }),
  updateApplicationStatus: (id, payload) => api(`/applications/${id}/status`, { method: 'PATCH', body: JSON.stringify(payload) }),
  notifications: (unreadOnly = false) => api(`/notifications?unread_only=${unreadOnly}`),
  markNotificationRead: (id) => api(`/notifications/${id}/read`, { method: 'PATCH' }),
  profile: () => api('/profile/me'),
  resume: () => api('/resume/me'),
  updateProfile: (payload) => api('/profile', { method: 'PUT', body: JSON.stringify(payload) }),
  createProfile: (payload) => api('/profile', { method: 'POST', body: JSON.stringify(payload) }),
  resumeUpload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api('/resume/upload', { method: 'POST', body: form })
  },
  sources: () => api('/job-sources'),
  sourceCapabilities: () => api('/job-sources/capabilities'),
}

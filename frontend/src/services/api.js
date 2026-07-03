import axios from 'axios'

const TOKEN_KEY = 'job_agent_token'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export const authApi = {
  register: (payload) => api.post('/auth/register', payload).then((r) => r.data),
  login: (payload) => api.post('/auth/login', payload).then((r) => r.data),
  verifyEmail: (token) => api.post('/auth/verify-email', { token }).then((r) => r.data),
  resendVerification: (email) => api.post('/auth/resend-verification', { email }).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
  mfaVerify: (payload) => api.post('/auth/mfa/verify', payload).then((r) => r.data),
  mfaSetup: () => api.post('/auth/mfa/setup').then((r) => r.data),
  mfaConfirm: (code) => api.post('/auth/mfa/confirm', { code }).then((r) => r.data),
  mfaDisable: (payload) => api.post('/auth/mfa/disable', payload).then((r) => r.data),
}

export const dashboardApi = {
  summary: () => api.get('/dashboard/summary').then((r) => r.data),
}

export function getErrorMessage(err, fallback) {
  if (err.response?.status === 429) {
    return "You've made too many attempts. Please wait a while before trying again."
  }
  return err.response?.data?.detail || err.response?.data?.error || fallback
}

export { TOKEN_KEY }
export default api

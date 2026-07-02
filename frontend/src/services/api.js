import axios from 'axios';

const API_BASE = '/api';
const TOKEN_KEY = 'job_agent_token';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  tokenKey: TOKEN_KEY,
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token) => localStorage.setItem(TOKEN_KEY, token),
  clearToken: () => localStorage.removeItem(TOKEN_KEY),
  register: (name, email, password) => api.post('/auth/register', { name, email, password }),
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    return axios.post(`${API_BASE}/auth/login`, form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  me: () => api.get('/auth/me'),
};

export const profileApi = {
  get: () => api.get('/profile'),
  save: (data) => api.post('/profile', data),
};

export const resumeApi = {
  generate: (jobId) => api.post(`/resume/generate${jobId ? `?job_id=${jobId}` : ''}`),
  download: (filename) => `${API_BASE}/resume/download/${filename}`,
  coverLetter: (jobId) => api.post(`/resume/cover-letter?job_id=${jobId}`),
  parseUpload: (file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/resume/parse', form, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};

export const jobsApi = {
  search: (query, location) => api.get('/jobs/search', { params: { query, location } }),
  list: (params) => api.get('/jobs', { params }),
  triggerSearch: () => api.post('/jobs/trigger-search'),
};

export const applicationsApi = {
  list: (params) => api.get('/applications', { params }),
  updateStatus: (id, data) => api.put(`/applications/${id}/status`, data),
  stats: () => api.get('/applications/stats'),
  logs: (id) => api.get(`/applications/${id}/logs`),
};

export const skillsApi = {
  gaps: () => api.get('/skills/gaps'),
  progress: () => api.get('/skills/progress'),
  updateProgress: (data) => api.post('/skills/progress', data),
  recommendations: () => api.get('/skills/recommendations'),
};

export const reportsApi = {
  daily: () => api.get('/reports/daily'),
  history: (limit) => api.get('/reports/history', { params: { limit } }),
};

export const dashboardApi = {
  get: () => api.get('/dashboard'),
};

export default api;

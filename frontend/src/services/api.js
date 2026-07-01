import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

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
    return axios.post(`${API_BASE}/resume/parse`, form);
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

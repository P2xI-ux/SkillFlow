import { api } from '../../core/api.js';

export const loginApi = (payload) => api('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) });
export const registerApi = (payload) => api('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });

import { api } from '../../core/api.js';

export const fetchTests = () => api('/api/tests', { headers: {} });
export const fetchTestById = (id) => api(`/api/tests/${id}`);
export const submitAttemptApi = (testId, payload) => api(`/api/tests/${testId}/attempt`, { method: 'POST', body: JSON.stringify(payload) });
export const fetchMyTests = () => api('/api/tests?mine=true');
export const createTestApi = (payload) => api('/api/tests', { method: 'POST', body: JSON.stringify(payload) });
export const submitTestApi = (id) => api(`/api/tests/${id}/submit`, { method: 'POST' });

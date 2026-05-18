import { api } from '../../core/api.js';

export const fetchMyProfile = () => api('/api/users/me');
export const fetchMyStats = () => api('/api/stats/me');
export const fetchMyAchievements = () => api('/api/achievements/me');
export const fetchSubjects = () => api('/api/subjects', { headers: {} });
export const fetchUniversityCatalog = () => api('/api/university/catalog', { headers: {} });

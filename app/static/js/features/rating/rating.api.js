import { api } from '../../core/api.js';

export const fetchRatings = () => api('/api/ratings', { headers: {} });

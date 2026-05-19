import { api } from '../../core/api.js';

export const fetchPendingTests = () => api('/api/tests/pending');
export const fetchPendingTestDetails = (testId) => api(`/api/tests/${testId}`);
export const moderateTest = (testId, action, comment = '') =>
  api(`/api/tests/${testId}/moderate`, {
    method: 'POST',
    body: JSON.stringify({ action, comment: action === 'approve' ? comment || 'Публикуем.' : comment }),
  });

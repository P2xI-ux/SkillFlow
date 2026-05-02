import { api } from '../../core/api.js';

export const fetchPendingTests = () => api('/api/tests/pending');
export const moderateTest = (testId, action) =>
  api(`/api/tests/${testId}/moderate`, {
    method: 'POST',
    body: JSON.stringify({ action, comment: action === 'approve' ? 'Публикуем.' : 'Нужно доработать.' }),
  });

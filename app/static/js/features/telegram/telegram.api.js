import { api } from '../../core/api.js';

export const requestTelegramLinkCode = () => api('/api/telegram/link-code', { method: 'POST' });

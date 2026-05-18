import { state } from '../../core/state.js';
import { el, hasElement, queryAll } from '../../core/dom.js';
import { fetchPendingTests } from './moderation.api.js';

export async function loadPendingTests(moderateHandler) {
  if (!hasElement('pendingList')) return;
  if (!state.token || state.currentUser?.role !== 'TEACHER') return (el('pendingList').innerHTML = 'Только преподаватель может модерировать тесты.');
  const items = await fetchPendingTests();
  el('pendingList').innerHTML = items.length
    ? items
        .map(
          (item) =>
            `<article class="list-item"><strong>${item.title}</strong><p>${item.author_name} · ${item.subject_name}</p><div class="inline-actions"><button class="primary-button compact" type="button" data-approve="${item.id}">Одобрить</button><button class="soft-button compact" type="button" data-reject="${item.id}">Отклонить</button></div></article>`,
        )
        .join('')
    : '<div class="empty-state">По вашим дисциплинам нет тестов в очереди.</div>';
  queryAll('[data-approve]').forEach((button) => button.addEventListener('click', () => moderateHandler(button.dataset.approve, 'approve')));
  queryAll('[data-reject]').forEach((button) => button.addEventListener('click', () => moderateHandler(button.dataset.reject, 'reject')));
}

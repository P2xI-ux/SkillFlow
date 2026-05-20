import { state } from '../../core/state.js';
import { el, hasElement, queryAll } from '../../core/dom.js';
import { escapeHtml, renderTestPreview } from '../../shared/templates.js';
import { fetchPendingTestDetails, fetchPendingTests } from './moderation.api.js';

export async function loadPendingTests(moderateHandler) {
  if (!hasElement('pendingList')) return;
  if (!state.token || state.currentUser?.role !== 'TEACHER') return (el('pendingList').innerHTML = 'Только преподаватель может модерировать тесты.');
  el('pendingList').innerHTML = '<div class="empty-state">Загружаем очередь модерации...</div>';
  if (hasElement('pendingPreview')) {
    el('pendingPreview').className = 'test-preview empty-state';
    el('pendingPreview').textContent = 'Выберите тест из очереди, чтобы посмотреть вопросы.';
  }
  let items = [];
  try {
    items = await fetchPendingTests();
  } catch (error) {
    el('pendingList').innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    return;
  }
  el('pendingList').innerHTML = items.length
    ? items
        .map(
          (item) =>
            `<article class="list-item test-list-item">
              <div>
                <strong>${escapeHtml(item.title)}</strong>
                <p>${escapeHtml(item.author_name)} · ${escapeHtml(item.subject_name)} · вопросов: ${escapeHtml(item.question_count)}</p>
              </div>
              <div class="inline-actions">
                <button class="soft-button compact" type="button" data-view-pending="${item.id}">Просмотр</button>
                <button class="primary-button compact" type="button" data-approve="${item.id}">Одобрить</button>
                <button class="soft-button compact" type="button" data-reject="${item.id}">Отклонить</button>
              </div>
            </article>`,
        )
        .join('')
    : '<div class="empty-state">По вашим дисциплинам нет тестов в очереди.</div>';
  if (!items.length && hasElement('pendingPreview')) {
    el('pendingPreview').className = 'test-preview empty-state';
    el('pendingPreview').innerHTML = 'Нечего просматривать: очередь модерации пуста.';
  }
  queryAll('[data-view-pending]').forEach((button) => button.addEventListener('click', () => renderPendingPreview(button.dataset.viewPending)));
  queryAll('[data-approve]').forEach((button) => button.addEventListener('click', () => moderateHandler(button.dataset.approve, 'approve')));
  queryAll('[data-reject]').forEach((button) => button.addEventListener('click', () => moderateHandler(button.dataset.reject, 'reject')));
}

export async function renderPendingPreview(testId) {
  if (!hasElement('pendingPreview')) return;
  el('pendingPreview').className = 'test-preview empty-state';
  el('pendingPreview').innerHTML = 'Загружаем содержимое теста...';
  try {
    const test = await fetchPendingTestDetails(testId);
    el('pendingPreview').className = 'test-preview';
    el('pendingPreview').innerHTML = renderTestPreview(test);
  } catch (error) {
    el('pendingPreview').className = 'test-preview empty-state';
    el('pendingPreview').textContent = error.message;
  }
}

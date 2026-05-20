import { state } from '../../core/state.js';
import { el, hasElement, queryAll } from '../../core/dom.js';
import { pageUrls } from '../../shared/constants.js';
import { escapeHtml, questionTypeLabel, renderAttemptQuestion, renderTestPreview, statusLabel } from '../../shared/templates.js';
import { fetchTestById } from './tests.api.js';

export async function openTest(testId, submitAttemptHandler, showDashboardScreen, allowRetake = false) {
  if (!state.token) return (window.location.href = pageUrls.auth);
  if (state.currentUser?.role !== 'STUDENT') return;
  const test = await fetchTestById(testId);
  state.selectedTest = test;
  state.selectedTestAllowRetake = allowRetake;
  showDashboardScreen('runner');
  const questionsHtml = test.questions
    .map(
      (question, index) => `
    <div class="question-block">
      <p class="helper-text">Вопрос ${index + 1} из ${test.questions.length}</p>
      <strong>${escapeHtml(question.text)}</strong>
      <p>${questionTypeLabel(question.question_type)} · ${question.points} баллов</p>
      ${renderAttemptQuestion(question)}
    </div>
  `,
    )
    .join('');
  el('testRunner').innerHTML = `
    <h3>${escapeHtml(test.title)}</h3>
    <p class="helper-text">${allowRetake ? 'Повторная попытка' : 'Новая попытка'} · вопросов: ${test.questions.length}</p>
    <form id="attemptForm">${questionsHtml}<button class="primary-button" type="submit">Завершить тест</button></form>
    <div id="attemptResult" class="message"></div>
  `;
  el('attemptForm').addEventListener('submit', submitAttemptHandler);
}

export function renderTests(tests, openTestHandler) {
  if (!hasElement('testsList')) return;
  if (!tests.length) {
    el('testsList').innerHTML = '<div class="empty-state">Опубликованных тестов пока нет.</div>';
    return;
  }
  el('testsList').innerHTML = tests
    .map(
      (test) => `
    <article class="list-item test-list-item">
      <div>
        <strong>${escapeHtml(test.title)}</strong>
        <p>${escapeHtml(test.description || 'Без описания')}</p>
        <p>${escapeHtml(test.subject_name)} · сложность ${escapeHtml(test.difficulty)} · вопросов: ${escapeHtml(test.question_count)}</p>
      </div>
      <button class="primary-button compact" type="button" data-open-test="${test.id}" data-test-attempted="${test.attempted ? '1' : '0'}">
        ${test.attempted ? 'Повторить' : 'Открыть'}
      </button>
    </article>
  `,
    )
    .join('');
  queryAll('[data-open-test]').forEach((button) =>
    button.addEventListener('click', () => {
      const isAttempted = button.dataset.testAttempted === '1';
      if (!isAttempted) {
        openTestHandler(button.dataset.openTest, false);
        return;
      }
      showRetakeModal(button.dataset.openTest, openTestHandler);
    }),
  );
}

function showRetakeModal(testId, openTestHandler) {
  let overlay = el('retakeModalOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'retakeModalOverlay';
    overlay.className = 'telegram-code-modal-overlay hidden';
    overlay.innerHTML = `
      <div class="telegram-code-modal" role="dialog" aria-modal="true" aria-labelledby="retakeModalTitle">
        <h3 id="retakeModalTitle">Повторное прохождение</h3>
        <p class="helper-text">Вы уже проходили этот тест. Новая попытка заменит вклад в рейтинг результатом повторного прохождения.</p>
        <div class="inline-actions">
          <button id="retakeModalConfirm" class="primary-button compact" type="button">Начать заново</button>
          <button id="retakeModalCancel" class="soft-button compact" type="button">Отмена</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    el('retakeModalCancel').addEventListener('click', () => overlay.classList.add('hidden'));
    overlay.addEventListener('click', (event) => {
      if (event.target === overlay) overlay.classList.add('hidden');
    });
  }
  el('retakeModalConfirm').onclick = () => {
    overlay.classList.add('hidden');
    openTestHandler(testId, true);
  };
  overlay.classList.remove('hidden');
}

export function renderMyTests(submitDraftHandler = null) {
  if (!hasElement('myTestsList')) return;
  if (state.currentUser?.role !== 'STUDENT') return;
  if (!state.myTests.length) {
    el('myTestsList').innerHTML = '<div class="empty-state">Созданные тесты появятся здесь.</div>';
    if (hasElement('myTestPreview')) el('myTestPreview').innerHTML = 'Черновики и отправленные тесты можно будет открыть здесь.';
    return;
  }
  el('myTestsList').innerHTML = state.myTests
    .map(
      (item) => `
        <article class="list-item test-list-item">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.subject_name)} · вопросов: ${escapeHtml(item.question_count)}</p>
            <span class="status-badge status-${item.status.toLowerCase()}">${statusLabel(item.status)}</span>
          </div>
          <div class="inline-actions test-card-actions">
            <button class="soft-button compact" type="button" data-view-my-test="${item.id}">Содержимое</button>
            ${
              item.status === 'DRAFT'
                ? `<button class="primary-button compact" type="button" data-submit-my-test="${item.id}">На модерацию</button>`
                : ''
            }
          </div>
        </article>
      `,
    )
    .join('');
  queryAll('[data-view-my-test]').forEach((button) => button.addEventListener('click', () => renderMyTestPreview(button.dataset.viewMyTest)));
  queryAll('[data-submit-my-test]').forEach((button) => button.addEventListener('click', () => submitDraftHandler?.(button.dataset.submitMyTest, button)));
}

async function renderMyTestPreview(testId) {
  if (!hasElement('myTestPreview')) return;
  el('myTestPreview').className = 'test-preview empty-state';
  el('myTestPreview').innerHTML = 'Загружаем содержимое теста...';
  try {
    const test = await fetchTestById(testId);
    el('myTestPreview').className = 'test-preview';
    el('myTestPreview').innerHTML = renderTestPreview(test);
  } catch (error) {
    el('myTestPreview').className = 'test-preview empty-state';
    el('myTestPreview').textContent = error.message;
  }
}

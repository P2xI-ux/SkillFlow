import { state } from '../../core/state.js';
import { el, hasElement, queryAll } from '../../core/dom.js';
import { pageUrls } from '../../shared/constants.js';
import { renderAttemptQuestion } from '../../shared/templates.js';
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
      (question) => `
    <div class="question-block">
      <strong>${question.text}</strong>
      <p>${question.question_type} · ${question.points} баллов</p>
      ${renderAttemptQuestion(question)}
    </div>
  `,
    )
    .join('');
  el('testRunner').innerHTML = `<h3>${test.title}</h3><form id="attemptForm">${questionsHtml}<button class="primary-button" type="submit">Завершить тест</button></form><div id="attemptResult" class="message"></div>`;
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
    <article class="list-item">
      <strong>${test.title}</strong>
      <p>${test.description || 'Без описания'}</p>
      <p>${test.subject_name} · сложность ${test.difficulty}</p>
      <button class="primary-button compact" type="button" data-open-test="${test.id}" data-test-attempted="${test.attempted ? '1' : '0'}">Открыть</button>
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
      const shouldRetake = window.confirm('Вы уже проходили этот тест. Нажмите "ОК", чтобы начать заново, или "Отмена", чтобы вернуться.');
      if (shouldRetake) openTestHandler(button.dataset.openTest, true);
    }),
  );
}

export function renderMyTests() {
  if (!hasElement('myTestsList')) return;
  if (!state.myTests.length) return (el('myTestsList').innerHTML = 'Созданные тесты появятся здесь.');
  el('myTestsList').innerHTML = state.myTests
    .map((item) => `<article class="list-item"><strong>${item.title}</strong><p>${item.subject_name}</p><p>Статус: ${item.status}</p></article>`)
    .join('');
}

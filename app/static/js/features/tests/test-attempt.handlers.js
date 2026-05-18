import { state } from '../../core/state.js';
import { el } from '../../core/dom.js';
import { setBusy } from '../../core/ui.js';
import { submitAttemptApi } from './tests.api.js';

export async function submitAttempt(event, { showAchievementToasts, loadPrivateData, loadPublicData }) {
  event.preventDefault();
  const submitButton = event.submitter || event.target.querySelector('button[type="submit"]');
  setBusy(submitButton, true, 'Проверяем...');
  const answers = state.selectedTest.questions.map((question) => {
    const answer = { question_id: question.id, selected_option_ids: [] };
    if (question.question_type === 'TEXT_ANSWER') {
      answer.text_answer = event.target.querySelector(`[name="q_text_${question.id}"]`)?.value || '';
    } else if (question.question_type === 'MATCHING') {
      answer.matching_answer = Object.fromEntries(
        [...event.target.querySelectorAll(`[name="q_match_${question.id}"]`)].map((input) => [input.dataset.left, input.value]),
      );
    } else {
      answer.selected_option_ids = [...event.target.querySelectorAll(`[name="q_${question.id}"]:checked`)].map((input) => Number(input.value));
    }
    return answer;
  });

  try {
    validateAttemptAnswers(state.selectedTest.questions, answers);
    const result = await submitAttemptApi(state.selectedTest.id, { answers, allow_retake: Boolean(state.selectedTestAllowRetake) });
    el('attemptResult').textContent = `Результат: ${result.score}/${result.max_score} (${result.percentage}%).`;
    showAchievementToasts(result.earned_achievements);
    await loadPrivateData();
    await loadPublicData();
  } catch (error) {
    el('attemptResult').textContent = error.message;
  } finally {
    setBusy(submitButton, false);
  }
}

function validateAttemptAnswers(questions, answers) {
  for (const question of questions) {
    const answer = answers.find((item) => item.question_id === question.id);
    if (!answer) throw new Error('Ответьте на все вопросы.');
    if (question.question_type === 'SINGLE_CHOICE' && answer.selected_option_ids.length !== 1) {
      throw new Error('Выберите один вариант в каждом вопросе с одиночным выбором.');
    }
    if (question.question_type === 'TEXT_ANSWER' && !answer.text_answer.trim()) {
      throw new Error('Заполните текстовые ответы.');
    }
    if (question.question_type === 'MATCHING') {
      const values = Object.values(answer.matching_answer || {});
      if (values.length !== question.matching_left.length || values.some((value) => !value)) {
        throw new Error('Заполните все пары соответствия.');
      }
    }
  }
}

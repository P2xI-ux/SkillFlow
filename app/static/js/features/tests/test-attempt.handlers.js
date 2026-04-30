import { state } from '../../core/state.js';
import { el } from '../../core/dom.js';
import { submitAttemptApi } from './tests.api.js';

export async function submitAttempt(event, { showAchievementToasts, loadPrivateData, loadPublicData }) {
  event.preventDefault();
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
    const result = await submitAttemptApi(state.selectedTest.id, { answers, allow_retake: false });
    el('attemptResult').textContent = `Результат: ${result.score}/${result.max_score} (${result.percentage}%).`;
    showAchievementToasts(result.earned_achievements);
    await loadPrivateData();
    await loadPublicData();
  } catch (error) {
    el('attemptResult').textContent = error.message;
  }
}

import { el, queryAll } from '../../core/dom.js';

export function buildConstructorPayload() {
  const questions = queryAll('.builder-question').map((questionElement) => {
    const type = questionElement.querySelector('[data-question-type]').value;
    const question = {
      text: questionElement.querySelector('[name="question_text"]').value.trim(),
      points: Number(questionElement.querySelector('[name="points"]').value),
      question_type: type,
      options: [],
    };
    if (type === 'TEXT_ANSWER') {
      question.correct_answer = questionElement.querySelector('.text-answer-input').value.trim();
    } else if (type === 'MATCHING') {
      question.matching_pairs = [...questionElement.querySelectorAll('.matching-pair')].map((row) => ({
        left: row.querySelector('.matching-left-input').value.trim(),
        right: row.querySelector('.matching-right-input').value.trim(),
      }));
    } else {
      question.options = [...questionElement.querySelectorAll('.answer-option')].map((row) => ({
        text: row.querySelector('.answer-text-input').value.trim(),
        is_correct: row.querySelector('input').checked,
      }));
    }
    return question;
  });
  if (!questions.length) throw new Error('Добавьте хотя бы один вопрос.');
  return {
    title: el('testTitleInput').value.trim(),
    description: el('testDescriptionInput').value.trim(),
    subject_id: Number(el('subjectSelect').value),
    difficulty: 3,
    questions,
  };
}

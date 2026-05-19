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
    validateQuestion(question);
    return question;
  });
  if (!questions.length) throw new Error('Добавьте хотя бы один вопрос.');
  if (!el('testTitleInput').value.trim()) throw new Error('Укажите название теста.');
  if (!Number(el('subjectSelect').value)) throw new Error('Выберите предмет.');
  return {
    title: el('testTitleInput').value.trim(),
    description: el('testDescriptionInput').value.trim(),
    subject_id: Number(el('subjectSelect').value),
    difficulty: Number(el('testDifficultySelect')?.value || 3),
    questions,
  };
}

function validateQuestion(question) {
  if (!question.text) throw new Error('Заполните текст каждого вопроса.');
  if (question.question_type === 'TEXT_ANSWER') {
    if (!question.correct_answer) throw new Error('Укажите правильный текстовый ответ.');
    return;
  }
  if (question.question_type === 'MATCHING') {
    const filledPairs = question.matching_pairs.filter((pair) => pair.left && pair.right);
    if (filledPairs.length < 2 || filledPairs.length !== question.matching_pairs.length) {
      throw new Error('Для соответствия нужны минимум две полностью заполненные пары.');
    }
    question.matching_pairs = filledPairs;
    return;
  }
  const filledOptions = question.options.filter((option) => option.text);
  if (filledOptions.length < 2 || filledOptions.length !== question.options.length) {
    throw new Error('В каждом вопросе с выбором нужны минимум два заполненных варианта.');
  }
  if (!filledOptions.some((option) => option.is_correct)) {
    throw new Error('Отметьте хотя бы один правильный вариант ответа.');
  }
  question.options = filledOptions;
}

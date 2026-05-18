import { state } from '../../core/state.js';
import { el, hasElement, queryAll } from '../../core/dom.js';
import { questionDifficultyOptions } from '../../shared/constants.js';

export function updateConstructorSummary() {
  if (hasElement('constructorSummary')) el('constructorSummary').textContent = `Вопросов: ${queryAll('.builder-question').length}`;
}

export function removeQuestionBlock(questionElement) {
  questionElement.remove();
  if (!queryAll('.builder-question').length && hasElement('constructorQuestions')) {
    el('constructorQuestions').className = 'stack empty-state';
    el('constructorQuestions').innerHTML = 'Добавьте первый вопрос.';
  }
  updateConstructorSummary();
}

export function addAnswerOption(questionElement) {
  const answersList = questionElement.querySelector('.answer-options');
  const optionIndex = answersList.children.length + 1;
  const row = document.createElement('div');
  row.className = 'answer-option';
  row.innerHTML = `<label class="answer-correct-toggle"></label><input class="answer-text-input" type="text" placeholder="Вариант ответа ${optionIndex}" required/><button class="soft-button compact" type="button" data-remove-option>Удалить</button>`;
  row.querySelector('[data-remove-option]').addEventListener('click', () => {
    row.remove();
    syncAnswerInputTypes(questionElement);
  });
  answersList.appendChild(row);
  syncAnswerInputTypes(questionElement);
}

export function syncAnswerInputTypes(questionElement) {
  const type = questionElement.querySelector('[data-question-type]').value;
  const questionIndex = questionElement.dataset.questionIndex;
  questionElement.querySelectorAll('.answer-option').forEach((row, index) => {
    row.querySelector('.answer-correct-toggle').innerHTML = `<input type="${type === 'SINGLE_CHOICE' ? 'radio' : 'checkbox'}" name="correct_${questionIndex}" ${index === 0 && type === 'SINGLE_CHOICE' ? 'checked' : ''}/><span>${type === 'SINGLE_CHOICE' ? 'Правильный' : 'Корректный'}</span>`;
  });
}

export function addMatchingPair(questionElement) {
  const pairsList = questionElement.querySelector('.matching-pairs');
  const row = document.createElement('div');
  row.className = 'matching-pair';
  row.innerHTML = '<input class="matching-left-input" type="text" placeholder="Левая часть" required/><input class="matching-right-input" type="text" placeholder="Правая часть" required/><button class="soft-button compact" type="button" data-remove-pair>Удалить</button>';
  row.querySelector('[data-remove-pair]').addEventListener('click', () => row.remove());
  pairsList.appendChild(row);
}

export function renderAnswerEditor(questionElement) {
  const type = questionElement.querySelector('[data-question-type]').value;
  const block = questionElement.querySelector('.answers-block');
  if (type === 'TEXT_ANSWER') {
    block.innerHTML = '<div class="field-group"><label>Правильный ответ</label><input class="text-answer-input" type="text" required /></div>';
    return;
  }
  if (type === 'MATCHING') {
    block.innerHTML = '<div class="section-title compact-title"><h3>Пары соответствия</h3><button class="soft-button compact" type="button" data-add-pair>Добавить пару</button></div><div class="matching-pairs stack"></div>';
    block.querySelector('[data-add-pair]').addEventListener('click', () => addMatchingPair(questionElement));
    addMatchingPair(questionElement);
    addMatchingPair(questionElement);
    return;
  }
  block.innerHTML = '<div class="section-title compact-title"><h3>Ответы</h3><button class="soft-button compact" type="button" data-add-option>Добавить вариант</button></div><div class="answer-options stack"></div>';
  block.querySelector('[data-add-option]').addEventListener('click', () => addAnswerOption(questionElement));
  addAnswerOption(questionElement);
  addAnswerOption(questionElement);
  syncAnswerInputTypes(questionElement);
}

export function addQuestionBlock() {
  if (!hasElement('constructorQuestions')) return;
  const container = el('constructorQuestions');
  if (container.classList.contains('empty-state')) {
    container.classList.remove('empty-state');
    container.innerHTML = '';
  }
  state.constructorQuestionCount += 1;
  const index = state.constructorQuestionCount;
  const question = document.createElement('section');
  question.className = 'builder-question inset-panel';
  question.dataset.questionIndex = String(index);
  question.innerHTML = `
    <div class="section-title compact-title"><div><p class="eyebrow">Вопрос ${index}</p><h3>Параметры вопроса</h3></div><button class="soft-button compact" type="button" data-remove-question>Удалить</button></div>
    <div class="field-row">
      <div class="field-group"><label>Сложность</label><select name="points">${questionDifficultyOptions.map((i) => `<option value="${i.value}">${i.label}</option>`).join('')}</select></div>
      <div class="field-group"><label>Тип вопроса</label><select name="question_type" data-question-type><option value="SINGLE_CHOICE">Одиночный выбор</option><option value="MULTIPLE_CHOICE">Множественный выбор</option><option value="TEXT_ANSWER">Текстовый ответ</option><option value="MATCHING">Соответствие</option></select></div>
    </div>
    <div class="field-group"><label>Текст вопроса</label><textarea name="question_text" required></textarea></div>
    <div class="answers-block"></div>
  `;
  container.appendChild(question);
  question.querySelector('[data-remove-question]').addEventListener('click', () => removeQuestionBlock(question));
  question.querySelector('[data-question-type]').addEventListener('change', () => renderAnswerEditor(question));
  renderAnswerEditor(question);
  updateConstructorSummary();
}

export function resetConstructor() {
  state.constructorQuestionCount = 0;
  if (hasElement('constructorQuestions')) {
    el('constructorQuestions').className = 'stack empty-state';
    el('constructorQuestions').innerHTML = 'Добавьте первый вопрос.';
  }
  updateConstructorSummary();
  addQuestionBlock();
}

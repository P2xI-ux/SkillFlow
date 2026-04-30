export function renderAttemptQuestion(question) {
  if (question.question_type === 'TEXT_ANSWER') {
    return `<textarea name="q_text_${question.id}" placeholder="Введите ответ"></textarea>`;
  }
  if (question.question_type === 'MATCHING') {
    return question.matching_left
      .map(
        (left) => `
      <label class="field-group">
        <span>${left}</span>
        <select name="q_match_${question.id}" data-left="${left}">
          <option value="">Выберите пару</option>
          ${question.matching_options.map((right) => `<option value="${right}">${right}</option>`).join('')}
        </select>
      </label>
    `,
      )
      .join('');
  }
  return question.options
    .map(
      (option) =>
        `<label><input type="${question.question_type === 'SINGLE_CHOICE' ? 'radio' : 'checkbox'}" name="q_${question.id}" value="${option.id}"/> ${option.text}</label>`,
    )
    .join('<br>');
}

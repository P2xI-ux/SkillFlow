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

export function statusLabel(status) {
  const labels = {
    DRAFT: 'Черновик',
    PENDING_MODERATION: 'На модерации',
    PUBLISHED: 'Опубликован',
    ARCHIVED: 'В архиве',
  };
  return labels[status] || status;
}

export function renderTestPreview(test) {
  const questions = test.questions
    .map((question, index) => {
      const options = question.options?.length
        ? `<ul>${question.options.map((option) => `<li>${option.text}</li>`).join('')}</ul>`
        : '';
      const matching = question.matching_left?.length
        ? `<p>${question.matching_left.join(' · ')}</p>`
        : '';
      return `
        <article class="preview-question">
          <div class="preview-question-head">
            <strong>${index + 1}. ${question.text}</strong>
            <span class="helper-chip">${question.points} баллов</span>
          </div>
          <p>${question.question_type}</p>
          ${options || matching || '<p>Текстовый ответ</p>'}
        </article>
      `;
    })
    .join('');
  return `
    <div class="preview-header">
      <div>
        <p class="eyebrow">${test.subject_name}</p>
        <h3>${test.title}</h3>
      </div>
      <span class="status-badge status-${test.status.toLowerCase()}">${statusLabel(test.status)}</span>
    </div>
    <p>${test.description || 'Без описания'}</p>
    <p class="helper-text">Автор: ${test.author_name} · сложность ${test.difficulty} · вопросов: ${test.questions.length}</p>
    <div class="preview-question-list">${questions}</div>
  `;
}

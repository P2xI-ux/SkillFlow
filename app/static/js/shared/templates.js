export function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function questionTypeLabel(type) {
  const labels = {
    SINGLE_CHOICE: 'Одиночный выбор',
    MULTIPLE_CHOICE: 'Множественный выбор',
    TEXT_ANSWER: 'Текстовый ответ',
    MATCHING: 'Соответствие',
  };
  return labels[type] || type;
}

export function renderAttemptQuestion(question) {
  if (question.question_type === 'TEXT_ANSWER') {
    return `<textarea name="q_text_${escapeHtml(question.id)}" placeholder="Введите ответ"></textarea>`;
  }
  if (question.question_type === 'MATCHING') {
    return question.matching_left
      .map(
        (left) => `
      <label class="field-group">
        <span>${escapeHtml(left)}</span>
        <select name="q_match_${escapeHtml(question.id)}" data-left="${escapeHtml(left)}">
          <option value="">Выберите пару</option>
          ${question.matching_options.map((right) => `<option value="${escapeHtml(right)}">${escapeHtml(right)}</option>`).join('')}
        </select>
      </label>
    `,
      )
      .join('');
  }
  return question.options
    .map(
      (option) =>
        `<label><input type="${question.question_type === 'SINGLE_CHOICE' ? 'radio' : 'checkbox'}" name="q_${escapeHtml(question.id)}" value="${escapeHtml(option.id)}"/> ${escapeHtml(option.text)}</label>`,
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
        ? `<ul>${question.options.map((option) => `<li>${escapeHtml(option.text)}</li>`).join('')}</ul>`
        : '';
      const matching = question.matching_left?.length
        ? `<p>${question.matching_left.map(escapeHtml).join(' · ')}</p>`
        : '';
      return `
        <article class="preview-question">
          <div class="preview-question-head">
            <strong>${index + 1}. ${escapeHtml(question.text)}</strong>
            <span class="helper-chip">${question.points} баллов</span>
          </div>
          <p>${questionTypeLabel(question.question_type)}</p>
          ${options || matching || '<p>Текстовый ответ</p>'}
        </article>
      `;
    })
    .join('');
  return `
    <div class="preview-header">
      <div>
        <p class="eyebrow">${escapeHtml(test.subject_name)}</p>
        <h3>${escapeHtml(test.title)}</h3>
      </div>
      <span class="status-badge status-${test.status.toLowerCase()}">${statusLabel(test.status)}</span>
    </div>
    <p>${escapeHtml(test.description || 'Без описания')}</p>
    <p class="helper-text">Автор: ${escapeHtml(test.author_name)} · сложность ${escapeHtml(test.difficulty)} · вопросов: ${test.questions.length}</p>
    <div class="preview-question-list">${questions}</div>
  `;
}

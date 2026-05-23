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
      let answersHtml = '';
      if (question.question_type === 'SINGLE_CHOICE' || question.question_type === 'MULTIPLE_CHOICE') {
        answersHtml = `
          <div class="preview-options">
            <strong>Варианты ответов:</strong>
            <ul style="margin-top: 4px; padding-left: 20px; list-style-type: disc;">
              ${question.options.map((option) => `
                <li style="${option.is_correct ? 'color: #10b981; font-weight: 600;' : ''}">
                  ${escapeHtml(option.text)} ${option.is_correct ? '<span style="background: rgba(16, 185, 129, 0.15); color: #10b981; margin-left: 6px; padding: 2px 8px; font-size: 0.8rem; border-radius: 999px; font-weight: 500; display: inline-block;">✓ Правильный</span>' : ''}
                </li>
              `).join('')}
            </ul>
          </div>
        `;
      } else if (question.question_type === 'TEXT_ANSWER') {
        answersHtml = `
          <div class="preview-text-answer" style="margin-top: 4px;">
            Правильный ответ: <strong style="color: #10b981;">${escapeHtml(question.correct_answer || '—')}</strong>
          </div>
        `;
      } else if (question.question_type === 'MATCHING') {
        answersHtml = `
          <div class="preview-matching">
            <strong>Соответствия:</strong>
            <ul style="margin-top: 4px; padding-left: 20px; list-style-type: disc;">
              ${question.matching_pairs.map((pair) => `
                <li>
                  ${escapeHtml(pair.left)} <span style="color: var(--primary); font-weight: bold;">↔</span> ${escapeHtml(pair.right)}
                </li>
              `).join('')}
            </ul>
          </div>
        `;
      }
      return `
        <article class="preview-question">
          <div class="preview-question-head">
            <strong>${index + 1}. ${escapeHtml(question.text)}</strong>
            <span class="helper-chip">${question.points} баллов</span>
          </div>
          <p class="eyebrow" style="margin-top: 4px; margin-bottom: 8px;">${questionTypeLabel(question.question_type)}</p>
          ${answersHtml}
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

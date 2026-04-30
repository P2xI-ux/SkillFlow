import { state } from '../../core/state.js';
import { el, hasElement } from '../../core/dom.js';

export function getFilteredRatings() {
  const subjectName = el('ratingSubjectFilter')?.value || '';
  const faculty = el('ratingFacultyFilter')?.value || '';
  return state.ratings.filter((item) => (!subjectName || item.subject_name === subjectName) && (!faculty || item.faculty === faculty));
}

export function renderRatings() {
  if (!hasElement('ratingsList')) return;
  const ratings = getFilteredRatings();
  el('ratingsList').innerHTML = ratings.length
    ? ratings
        .map(
          (item) => `
      <div class="list-item">
        <div>
          <strong>#${item.position} ${item.student_name}</strong>
          <p>${item.subject_name} · ${item.faculty || '—'}</p>
        </div>
        <div class="rating-meta"><span>${item.total_score}</span><small>баллов</small></div>
      </div>
    `,
        )
        .join('')
    : '<div class="empty-state">Нет данных по выбранным фильтрам.</div>';
}

export function renderStudentRatings() {
  if (!hasElement('studentRatingsList')) return;
  const top = state.ratings.slice(0, 8);
  el('studentRatingsList').innerHTML = top.length
    ? top.map((item) => `<div class="list-item"><strong>#${item.position} ${item.student_name}</strong><p>${item.subject_name}: ${item.total_score}</p></div>`).join('')
    : '<div class="empty-state">Рейтинг появится после первых попыток.</div>';
}

export function renderTeacherStatsFilters() {
  if (!hasElement('teacherStatsSubject')) return;
  const names = [...new Set(state.ratings.map((item) => item.subject_name))];
  el('teacherStatsSubject').innerHTML = names.length ? names.map((name) => `<option value="${name}">${name}</option>`).join('') : '<option value="">Нет предметов</option>';
  renderTeacherStats();
}

export function renderTeacherStats() {
  if (!hasElement('teacherStatsBox')) return;
  const subjectName = el('teacherStatsSubject')?.value;
  const items = state.ratings.filter((item) => item.subject_name === subjectName).sort((a, b) => b.total_score - a.total_score);
  if (!items.length) {
    el('teacherStatsBox').innerHTML = '<div class="empty-state">Нет статистики по выбранному предмету.</div>';
    return;
  }
  const avg = Math.round(items.reduce((sum, item) => sum + item.total_score, 0) / items.length);
  el('teacherStatsBox').innerHTML = `
    <div class="list-item"><strong>Участников:</strong> ${items.length}</div>
    <div class="list-item"><strong>Средний балл:</strong> ${avg}</div>
    ${items.slice(0, 5).map((item) => `<div class="list-item"><strong>${item.student_name}</strong><p>${item.total_score} баллов · ${item.faculty || '—'}</p></div>`).join('')}
  `;
}

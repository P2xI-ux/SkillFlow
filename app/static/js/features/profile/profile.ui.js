import { state } from '../../core/state.js';
import { el, hasElement, queryAll } from '../../core/dom.js';

export function showDashboardScreen(screen) {
  state.currentScreen = screen || 'profile';
  queryAll('[data-dashboard-screen]').forEach((item) => {
    item.classList.toggle('is-hidden', item.dataset.dashboardScreen !== state.currentScreen);
  });
  queryAll('[data-dashboard-target]').forEach((button) => {
    button.classList.toggle('active', button.dataset.dashboardTarget === state.currentScreen);
  });
}

export function renderProfile() {
  if (!hasElement('profileBox')) return;
  if (!state.currentUser) {
    el('profileBox').className = 'profile-grid empty-state';
    el('profileBox').innerHTML = 'Войдите, чтобы увидеть профиль.';
    return;
  }
  const user = state.currentUser;
  const teacherSubjects = user.teaching_subjects?.length ? user.teaching_subjects.map((s) => s.name).join(', ') : '—';
  const profileRows = [
    ['Пользователь', user.full_name],
    ['Email', user.email],
    ['Роль', user.role === 'STUDENT' ? 'Студент' : 'Преподаватель'],
    ['Институт', user.faculty || '—'],
  ];
  if (user.role === 'STUDENT') {
    profileRows.push(['Группа / курс', `${user.study_group || '—'} / ${user.course || '—'}`], ['Направление', user.program_code || '—']);
  } else {
    profileRows.push(['Кафедра', user.department || '—'], ['Дисциплины', teacherSubjects]);
  }
  profileRows.push(['Telegram', user.telegram_id || 'не привязан']);
  el('profileBox').className = 'profile-grid';
  el('profileBox').innerHTML = profileRows.map(([label, value]) => `<div><strong>${label}</strong><br>${value}</div>`).join('');
}

export function renderRoleCapabilities() {
  if (!hasElement('roleCapabilities')) return;
  if (!state.currentUser) {
    el('roleCapabilities').innerHTML = '<div class="empty-state">После входа отобразятся доступные функциональные блоки.</div>';
    return;
  }
  if (state.currentUser.role === 'TEACHER') {
    el('roleCapabilities').innerHTML = `
      <div class="capability-item"><strong>Модерация тестов</strong><p>Проверка и публикация тестов только по вашим предметам.</p></div>
      <div class="capability-item"><strong>Статистика по предметам</strong><p>Анализ рейтинга студентов в разрезе дисциплины.</p></div>
      <div class="capability-item"><strong>Личная информация</strong><p>Профиль и привязка Telegram.</p></div>
    `;
  } else {
    el('roleCapabilities').innerHTML = `
      <div class="capability-item"><strong>Создание теста</strong><p>Конструктор с вопросами и ответами.</p></div>
      <div class="capability-item"><strong>Рейтинг и результат теста</strong><p>Каталог тестов, прохождение и динамика баллов.</p></div>
      <div class="capability-item"><strong>Личная информация</strong><p>Профиль, статистика и привязка Telegram.</p></div>
    `;
  }
}

export function toggleRoleWidgets() {
  const role = state.currentUser?.role;
  queryAll('.student-only').forEach((item) => item.classList.toggle('hidden-by-role', role !== 'STUDENT'));
  queryAll('.teacher-only').forEach((item) => item.classList.toggle('hidden-by-role', role !== 'TEACHER'));
  const studentScreens = new Set(['builder', 'runner', 'stats']);
  const teacherScreens = new Set(['moderation', 'teacherStats']);
  if ((role !== 'STUDENT' && studentScreens.has(state.currentScreen)) || (role !== 'TEACHER' && teacherScreens.has(state.currentScreen))) {
    showDashboardScreen('profile');
  } else {
    showDashboardScreen(state.currentScreen);
  }
}

export function renderStats(stats) {
  if (!hasElement('statsBox')) return;
  if (!stats) {
    el('statsBox').innerHTML = 'После прохождения тестов здесь появится статистика.';
    return;
  }
  const breakdown = Object.entries(stats.subject_breakdown)
    .map(([subject, score]) => `<li>${subject}: ${score}</li>`)
    .join('') || '<li>Пока нет рейтинга</li>';
  const attempts = stats.latest_attempts.map((attempt) => `<li>${attempt.subject_name}: ${attempt.score}/${attempt.max_score}</li>`).join('') || '<li>Нет попыток</li>';
  el('statsBox').innerHTML = `
    <div class="list-item"><strong>Пройдено тестов:</strong> ${stats.tests_completed}</div>
    <div class="list-item"><strong>Средний результат:</strong> ${stats.average_score_percent}%</div>
    <div class="list-item"><strong>Суммарный рейтинг:</strong> ${stats.rating_total}</div>
    <div class="list-item"><strong>Баллы по предметам:</strong><ul>${breakdown}</ul></div>
    <div class="list-item"><strong>Последние попытки:</strong><ul>${attempts}</ul></div>
  `;
}

export function renderAchievements(items) {
  if (!hasElement('achievementsList')) return;
  el('achievementsList').innerHTML = items.length
    ? items.map((item) => `<div class="list-item"><strong>${item.name}</strong><p>${item.description}</p></div>`).join('')
    : '<div class="empty-state">Достижения ещё не открыты.</div>';
}

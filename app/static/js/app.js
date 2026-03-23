const state = {
  token: localStorage.getItem('skillflow_token') || '',
  currentUser: null,
  subjects: [],
  selectedTest: null,
  myTests: [],
  currentPage: document.body.dataset.page || 'home',
  currentTheme: localStorage.getItem('skillflow_theme') || 'light',
  currentRole: 'STUDENT',
};

const pageUrls = {
  home: '/',
  auth: '/auth',
  dashboard: '/dashboard',
};

const roleCapabilities = {
  STUDENT: [
    { title: 'Пройти тест', text: 'Откройте каталог, выберите подходящий тест и отправьте попытку.' },
    { title: 'Следить за рейтингом', text: 'Сравнивайте результаты с другими студентами и отслеживайте прогресс.' },
    { title: 'Создать тест', text: 'Соберите черновик теста и отправьте его на модерацию.' },
  ],
  TEACHER: [
    { title: 'Модерация тестов', text: 'Проверяйте новые материалы по предмету и публикуйте лучшие тесты.' },
    { title: 'Управление контентом', text: 'Следите за качеством вопросов и соответствием учебной программе.' },
    { title: 'Контроль активности', text: 'Используйте каталог и рейтинг как обзор вовлечённости студентов.' },
  ],
  ADMIN: [
    { title: 'Следить за платформой', text: 'Контролируйте метрики использования и ключевые сценарии пользователей.' },
    { title: 'Поддерживать стабильность', text: 'Управляйте инфраструктурой и общими настройками системы.' },
    { title: 'Развивать продукт', text: 'Используйте аналитику для улучшения пользовательского опыта.' },
  ],
};

const dashboardContent = {
  STUDENT: {
    title: 'Ваше пространство для учёбы и практики',
    lead: 'Проходите тесты, отслеживайте результаты, открывайте достижения и создавайте собственные материалы.',
    cards: [
      { title: 'Что сделать сейчас', text: 'Откройте тест из каталога и проверьте, какие темы стоит повторить в первую очередь.' },
      { title: 'Как расти быстрее', text: 'Сравнивайте последние попытки, следите за рейтингом и закрепляйте сильные результаты.' },
      { title: 'Следующий шаг', text: 'Создайте свой тест и отправьте его на модерацию, чтобы делиться знаниями с другими.' },
    ],
  },
  TEACHER: {
    title: 'Кабинет преподавателя и модератора',
    lead: 'Контролируйте качество контента, проверяйте новые тесты и поддерживайте учебный процесс без лишней рутины.',
    cards: [
      { title: 'Главный фокус', text: 'Проверьте очередь модерации и опубликуйте материалы, которые готовы к использованию.' },
      { title: 'Польза для студентов', text: 'Поддерживайте понятные и корректные задания, чтобы обучение оставалось прозрачным и полезным.' },
      { title: 'Рабочий ритм', text: 'Используйте каталог и активность пользователей как быстрый обзор вовлечённости по предметам.' },
    ],
  },
  ADMIN: {
    title: 'Панель управления платформой',
    lead: 'Держите под контролем состояние сервиса, роли пользователей и ключевые продуктовые показатели.',
    cards: [
      { title: 'Операционный обзор', text: 'Отслеживайте стабильность сервиса и актуальность пользовательских сценариев.' },
      { title: 'Управление доступом', text: 'Следите за ролями и корректностью настроек для разных сегментов аудитории.' },
      { title: 'Развитие продукта', text: 'Используйте сигналы активности и рейтинга для улучшения платформы.' },
    ],
  },
};

const api = async (path, options = {}) => {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  const data = response.headers.get('content-type')?.includes('application/json') ? await response.json() : null;
  if (!response.ok) throw new Error(data?.detail || 'Ошибка запроса');
  return data;
};

const el = (id) => document.getElementById(id);
const queryAll = (selector) => [...document.querySelectorAll(selector)];
const hasElement = (id) => Boolean(el(id));

async function bootstrap() {
  applyTheme(state.currentTheme);
  bindThemeToggle();
  bindTabs();
  bindRoleSwitch();
  bindForms();
  updateRoleUI();
  updateAuthControls();

  await loadPublicData();

  if (state.currentPage === 'dashboard') {
    if (!state.token) {
      window.location.href = pageUrls.auth;
      return;
    }
    await loadSubjects();
  }

  if (state.token) {
    try {
      await loadProfile();
      await loadPrivateData();
      if (state.currentPage === 'auth') {
        window.location.href = pageUrls.dashboard;
        return;
      }
    } catch {
      logout({ redirect: false });
    }
  }
}

function bindThemeToggle() {
  if (!hasElement('themeToggleBtn')) return;
  el('themeToggleBtn').addEventListener('click', () => {
    const nextTheme = state.currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(nextTheme);
  });
}

function applyTheme(theme) {
  state.currentTheme = theme;
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('skillflow_theme', theme);
}

function bindTabs() {
  if (!queryAll('.tab').length) return;
  queryAll('.tab').forEach((button) => {
    button.addEventListener('click', () => {
      queryAll('.tab').forEach((tab) => tab.classList.remove('active'));
      button.classList.add('active');
      el('loginForm')?.classList.toggle('hidden', button.dataset.tab !== 'login');
      el('registerForm')?.classList.toggle('hidden', button.dataset.tab !== 'register');
      if (hasElement('authMessage')) el('authMessage').textContent = '';
    });
  });
}

function bindRoleSwitch() {
  if (!hasElement('roleSwitch')) return;
  queryAll('#roleSwitch .role-pill').forEach((button) => {
    button.addEventListener('click', () => {
      state.currentRole = button.dataset.role;
      queryAll('#roleSwitch .role-pill').forEach((pill) => pill.classList.toggle('active', pill === button));
      updateRoleUI();
    });
  });
}

function updateRoleUI() {
  const isStudent = state.currentRole === 'STUDENT';
  if (hasElement('registerRole')) el('registerRole').value = state.currentRole;
  el('studentFields')?.classList.toggle('hidden', !isStudent);
  el('teacherFields')?.classList.toggle('hidden', isStudent);
  if (hasElement('loginRoleHint')) {
    el('loginRoleHint').innerHTML = isStudent
      ? '<strong>Студент:</strong> вход в каталог тестов, рейтинг и личную статистику.'
      : '<strong>Преподаватель:</strong> доступ к модерации тестов и контролю публикаций.';
  }
}

function bindForms() {
  el('loginForm')?.addEventListener('submit', login);
  el('registerForm')?.addEventListener('submit', register);
  el('createTestForm')?.addEventListener('submit', createTest);
  el('refreshTestsBtn')?.addEventListener('click', loadPublicData);
  el('loadPendingBtn')?.addEventListener('click', loadPendingTests);
  el('logoutBtn')?.addEventListener('click', () => logout({ redirect: true }));
  el('linkTelegramBtn')?.addEventListener('click', linkTelegram);
  el('submitLatestTestBtn')?.addEventListener('click', submitLatestTest);
  el('demoTeacherBtn')?.addEventListener('click', demoTeacherLogin);
}

function updateAuthControls() {
  const loggedIn = Boolean(state.token);
  queryAll('[data-auth-nav], [data-auth-cta]').forEach((link) => {
    link.textContent = loggedIn ? 'Личный кабинет' : 'Войти';
    link.setAttribute('href', loggedIn ? pageUrls.dashboard : pageUrls.auth);
  });
  if (hasElement('logoutBtn')) {
    el('logoutBtn').classList.toggle('hidden', !loggedIn);
  }
}

async function login(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    const data = await api('/api/auth/login', { method: 'POST', body: JSON.stringify(Object.fromEntries(form)) });
    await setSession(data);
    if (hasElement('authMessage')) el('authMessage').textContent = 'Вход выполнен успешно.';
    window.location.href = pageUrls.dashboard;
  } catch (error) {
    if (hasElement('authMessage')) el('authMessage').textContent = error.message;
  }
}

async function register(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = Object.fromEntries(form);
  if (!payload.course) payload.course = null;
  if (payload.role === 'TEACHER') payload.study_group = null;
  if (payload.role === 'STUDENT') payload.department = null;
  try {
    const data = await api('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });
    await setSession(data);
    if (hasElement('authMessage')) el('authMessage').textContent = 'Регистрация выполнена.';
    window.location.href = pageUrls.dashboard;
  } catch (error) {
    if (hasElement('authMessage')) el('authMessage').textContent = error.message;
  }
}

async function demoTeacherLogin() {
  try {
    await api('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: 'teacher@skillflow.local',
        password: 'teacher123',
        full_name: 'Demo Teacher',
        role: 'TEACHER',
        faculty: 'Информатика',
        department: 'Кафедра ИТ'
      })
    }).catch(() => null);
  } catch {}
  try {
    const data = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: 'teacher@skillflow.local', password: 'teacher123' })
    });
    await setSession(data);
    window.location.href = pageUrls.dashboard;
  } catch (error) {
    if (hasElement('authMessage')) {
      el('authMessage').textContent = error.message;
    } else {
      alert(error.message);
    }
  }
}

async function setSession(data) {
  state.token = data.access_token;
  localStorage.setItem('skillflow_token', state.token);
  state.currentUser = data.user;
  state.currentRole = data.user.role;
  updateRoleUI();
  updateAuthControls();
  renderRoleCapabilities();
  toggleRoleWidgets();
  renderDashboardSpotlight();
  await Promise.all([loadProfile(), loadPrivateData()]);
}

function logout({ redirect = true } = {}) {
  state.token = '';
  state.currentUser = null;
  state.selectedTest = null;
  localStorage.removeItem('skillflow_token');
  updateAuthControls();
  renderProfile();
  renderStats();
  renderRoleCapabilities();
  renderDashboardSpotlight();
  toggleRoleWidgets();
  if (hasElement('testRunner')) el('testRunner').innerHTML = 'Выберите тест из каталога.';
  if (hasElement('achievementsList')) el('achievementsList').innerHTML = '';
  if (hasElement('pendingList')) el('pendingList').innerHTML = 'Только преподаватель может модерировать тесты.';
  loadPublicData();
  if (redirect) window.location.href = pageUrls.home;
}

async function loadSubjects() {
  if (!hasElement('subjectSelect')) return;
  state.subjects = await api('/api/subjects', { headers: {} });
  el('subjectSelect').innerHTML = state.subjects.map((subject) => `<option value="${subject.id}">${subject.name}</option>`).join('');
}

async function loadProfile() {
  if (!state.token) {
    renderProfile();
    return;
  }
  state.currentUser = await api('/api/users/me');
  state.currentRole = state.currentUser.role;
  updateRoleUI();
  updateAuthControls();
  renderProfile();
  renderRoleCapabilities();
  renderDashboardSpotlight();
  toggleRoleWidgets();
}

function renderProfile() {
  if (!hasElement('profileBox')) return;
  if (!state.currentUser) {
    el('profileBox').className = 'profile-grid empty-state';
    el('profileBox').innerHTML = 'Войдите, чтобы увидеть профиль.';
    return;
  }
  const user = state.currentUser;
  el('profileBox').className = 'profile-grid';
  el('profileBox').innerHTML = [
    ['Пользователь', user.full_name],
    ['Email', user.email],
    ['Роль', user.role],
    ['Факультет / кафедра', user.faculty || user.department || '—'],
    ['Группа / курс', `${user.study_group || '—'} / ${user.course || '—'}`],
    ['Telegram', user.telegram_id || 'не привязан'],
  ].map(([label, value]) => `<div><strong>${label}</strong><br>${value}</div>`).join('');
}

function renderRoleCapabilities() {
  if (!hasElement('roleCapabilities')) return;
  const box = el('roleCapabilities');
  if (!state.currentUser) {
    box.className = 'capability-list empty-state';
    box.innerHTML = 'После входа здесь появится список доступных действий.';
    return;
  }
  const items = roleCapabilities[state.currentUser.role] || [];
  box.className = 'capability-list';
  box.innerHTML = items.map((item) => `
    <div class="capability-item">
      <strong>${item.title}</strong>
      <p>${item.text}</p>
    </div>
  `).join('');
}

function renderDashboardSpotlight() {
  if (!hasElement('dashboardRoleSpotlight')) return;
  const role = state.currentUser?.role || 'STUDENT';
  const config = dashboardContent[role] || dashboardContent.STUDENT;
  el('dashboardHeading').textContent = config.title;
  el('dashboardLead').textContent = config.lead;
  el('dashboardRoleSpotlight').innerHTML = `
    <div class="section-title compact-title">
      <div>
        <p class="eyebrow">Сценарий роли</p>
        <h3>${config.title}</h3>
      </div>
    </div>
    <div class="spotlight-grid">
      ${config.cards.map((card) => `
        <div class="spotlight-card inset-panel">
          <strong>${card.title}</strong>
          <p>${card.text}</p>
        </div>
      `).join('')}
    </div>
  `;
}

function toggleRoleWidgets() {
  const role = state.currentUser?.role;
  queryAll('.student-only').forEach((item) => item.classList.toggle('hidden-by-role', role === 'TEACHER' || role === 'ADMIN'));
  queryAll('.teacher-only').forEach((item) => item.classList.toggle('hidden-by-role', role !== 'TEACHER'));
}

async function loadPublicData() {
  const [tests, ratings] = await Promise.all([api('/api/tests', { headers: {} }), api('/api/ratings', { headers: {} })]);
  renderTests(tests);
  renderRatings(ratings);
}

async function loadPrivateData() {
  if (!state.token) return;
  await Promise.all([loadMyStats(), loadAchievements(), loadMyTests()]);
  if (state.currentUser?.role === 'TEACHER') await loadPendingTests();
}

async function loadMyStats() {
  if (!state.token || state.currentUser?.role !== 'STUDENT') return renderStats();
  const stats = await api('/api/stats/me');
  renderStats(stats);
}

function renderStats(stats) {
  if (!hasElement('statsBox')) return;
  if (!stats) {
    el('statsBox').className = 'stack empty-state';
    el('statsBox').innerHTML = 'После прохождения тестов здесь появится статистика.';
    return;
  }
  const breakdown = Object.entries(stats.subject_breakdown).map(([subject, score]) => `<li>${subject}: ${score}</li>`).join('') || '<li>Пока нет рейтинга</li>';
  const attempts = stats.latest_attempts.map((attempt) => `<li>${attempt.subject_name}: ${attempt.score}/${attempt.max_score}</li>`).join('') || '<li>Нет попыток</li>';
  el('statsBox').className = 'stack';
  el('statsBox').innerHTML = `
    <div class="list-item"><strong>Пройдено тестов:</strong> ${stats.tests_completed}</div>
    <div class="list-item"><strong>Средний результат:</strong> ${stats.average_score_percent}%</div>
    <div class="list-item"><strong>Суммарный рейтинг:</strong> ${stats.rating_total}</div>
    <div class="list-item"><strong>Баллы по предметам:</strong><ul>${breakdown}</ul></div>
    <div class="list-item"><strong>Последние попытки:</strong><ul>${attempts}</ul></div>
  `;
}

async function loadAchievements() {
  if (!hasElement('achievementsList')) return;
  if (!state.token || state.currentUser?.role !== 'STUDENT') return (el('achievementsList').innerHTML = '');
  const items = await api('/api/achievements/me');
  el('achievementsList').innerHTML = items.length
    ? items.map((item) => `<div class="list-item"><strong>${item.name}</strong><p>${item.description}</p></div>`).join('')
    : '<div class="empty-state">Достижения ещё не открыты.</div>';
}

function renderTests(tests) {
  if (!hasElement('testsList')) return;
  const list = el('testsList');
  if (!tests.length) {
    list.innerHTML = '<div class="empty-state">Опубликованных тестов пока нет.</div>';
    return;
  }
  list.innerHTML = tests.map((test) => `
    <article class="list-item">
      <strong>${test.title}</strong>
      <p>${test.description || 'Без описания'}</p>
      <p>${test.subject_name} • сложность ${test.difficulty} • вопросов ${test.question_count}</p>
      <button class="primary-button compact" type="button" data-open-test="${test.id}">Открыть</button>
    </article>
  `).join('');
  list.querySelectorAll('[data-open-test]').forEach((button) => button.addEventListener('click', () => openTest(button.dataset.openTest)));
}

async function openTest(testId) {
  if (!state.token) {
    window.location.href = pageUrls.auth;
    return;
  }
  if (state.currentPage !== 'dashboard') {
    window.location.href = pageUrls.dashboard;
    return;
  }
  const test = await api(`/api/tests/${testId}`);
  state.selectedTest = test;
  const questionsHtml = test.questions.map((question) => `
    <div class="question-block">
      <strong>${question.text}</strong>
      <p>${question.question_type} • ${question.points} баллов</p>
      ${question.options.map((option) => `
        <label>
          <input type="${question.question_type === 'SINGLE_CHOICE' ? 'radio' : 'checkbox'}" name="q_${question.id}" value="${option.id}" /> ${option.text}
        </label>
      `).join('<br>')}
    </div>
  `).join('');
  el('testRunner').innerHTML = `
    <h3>${test.title}</h3>
    <p>${test.subject_name} • сложность ${test.difficulty}</p>
    <form id="attemptForm">${questionsHtml}<button class="primary-button" type="submit">Завершить тест</button></form>
    <div id="attemptResult" class="message"></div>
  `;
  el('attemptForm').addEventListener('submit', submitAttempt);
}

async function submitAttempt(event) {
  event.preventDefault();
  const answers = state.selectedTest.questions.map((question) => ({
    question_id: question.id,
    selected_option_ids: [...event.target.querySelectorAll(`[name="q_${question.id}"]:checked`)].map((input) => Number(input.value))
  }));
  const result = await api(`/api/tests/${state.selectedTest.id}/attempt`, {
    method: 'POST',
    body: JSON.stringify({ answers })
  });
  el('attemptResult').textContent = `Результат: ${result.score}/${result.max_score} (${result.percentage}%). Рейтинг +${result.rating_delta}. Достижения: ${result.earned_achievements.join(', ') || 'нет новых'}.`;
  await loadPrivateData();
  await loadPublicData();
}

async function createTest(event) {
  event.preventDefault();
  if (!state.token) return (el('createMessage').textContent = 'Нужна авторизация.');
  const form = new FormData(event.target);
  let questions;
  try {
    questions = JSON.parse(form.get('questions_json')).questions;
  } catch {
    el('createMessage').textContent = 'Не удалось разобрать JSON с вопросами.';
    return;
  }
  const payload = {
    title: form.get('title'),
    description: form.get('description'),
    subject_id: Number(form.get('subject_id')),
    difficulty: Number(form.get('difficulty')),
    questions,
  };
  try {
    const test = await api('/api/tests', { method: 'POST', body: JSON.stringify(payload) });
    el('createMessage').textContent = `Черновик "${test.title}" создан.`;
    await loadMyTests();
  } catch (error) {
    el('createMessage').textContent = error.message;
  }
}

async function loadMyTests() {
  if (!state.token) {
    state.myTests = [];
    return;
  }
  state.myTests = await fetch('/api/tests?mine=true', { headers: { Authorization: `Bearer ${state.token}` } }).then((response) => response.json());
}

async function submitLatestTest() {
  if (!state.myTests?.length) return (el('createMessage').textContent = 'Сначала создайте тест.');
  const draft = state.myTests.find((item) => item.status === 'DRAFT');
  if (!draft) return (el('createMessage').textContent = 'У вас нет черновиков для отправки.');
  const test = await api(`/api/tests/${draft.id}/submit`, { method: 'POST' });
  el('createMessage').textContent = `Тест "${test.title}" отправлен на модерацию.`;
  await loadMyTests();
}

async function loadPendingTests() {
  if (!hasElement('pendingList')) return;
  if (!state.token || state.currentUser?.role !== 'TEACHER') {
    el('pendingList').innerHTML = 'Только преподаватель может модерировать тесты.';
    return;
  }
  const items = await api('/api/tests/pending');
  el('pendingList').innerHTML = items.length
    ? items.map((item) => `
      <article class="list-item">
        <strong>${item.title}</strong>
        <p>${item.author_name} • ${item.subject_name}</p>
        <div class="inline-actions">
          <button class="primary-button compact" type="button" data-approve="${item.id}">Одобрить</button>
          <button class="soft-button compact" type="button" data-reject="${item.id}">Отклонить</button>
        </div>
      </article>
    `).join('')
    : '<div class="empty-state">Очередь модерации пуста.</div>';
  el('pendingList').querySelectorAll('[data-approve]').forEach((button) => button.addEventListener('click', () => moderate(button.dataset.approve, 'approve')));
  el('pendingList').querySelectorAll('[data-reject]').forEach((button) => button.addEventListener('click', () => moderate(button.dataset.reject, 'reject')));
}

async function moderate(testId, action) {
  await api(`/api/tests/${testId}/moderate`, {
    method: 'POST',
    body: JSON.stringify({ action, comment: action === 'approve' ? 'Публикуем в каталог.' : 'Нужно доработать формулировки.' })
  });
  await loadPendingTests();
  await loadPublicData();
  await loadAchievements();
}

function renderRatings(ratings) {
  if (!hasElement('ratingsList')) return;
  el('ratingsList').innerHTML = ratings.length
    ? ratings.map((item) => `
      <div class="list-item">
        <div>
          <strong>#${item.position} ${item.student_name}</strong>
          <p>${item.subject_name}</p>
        </div>
        <div class="rating-meta">
          <span>${item.total_score}</span>
          <small>баллов</small>
        </div>
      </div>
    `).join('')
    : '<div class="empty-state">Рейтинг появится после первых прохождений.</div>';
}

async function linkTelegram() {
  if (!state.token) return;
  const data = await api('/api/telegram/link-code', { method: 'POST' });
  alert(`Код для привязки Telegram: ${data.code}`);
  await loadProfile();
}

bootstrap();

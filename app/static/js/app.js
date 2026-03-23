const state = {
  token: localStorage.getItem('skillflow_token') || '',
  currentUser: null,
  subjects: [],
  selectedTest: null,
  myTests: [],
  currentPage: document.body.dataset.page || 'home',
  currentTheme: localStorage.getItem('skillflow_theme') || 'light',
  currentRole: 'STUDENT',
  constructorQuestionCount: 0,
};

const pageUrls = {
  home: '/',
  auth: '/auth',
  dashboard: '/dashboard',
};

const pageUrls = {
  home: '/',
  auth: '/auth',
  dashboard: '/dashboard',
};

const roleCapabilities = {
  STUDENT: [
    { title: 'Прохождение тестов', text: 'Открывайте опубликованные тесты, проходите попытки и получайте обратную связь.' },
    { title: 'Личная аналитика', text: 'Следите за статистикой, рейтингом и достижениями по своим результатам.' },
    { title: 'Конструктор тестов', text: 'Собирайте собственные тесты в визуальном конструкторе и отправляйте их на модерацию.' },
  ],
  TEACHER: [
    { title: 'Модерация по дисциплинам', text: 'Проверяйте только те тесты, которые относятся к дисциплинам, закреплённым за вами.' },
    { title: 'Контроль качества', text: 'Оценивайте формулировки, типы вопросов и корректность вариантов ответа.' },
    { title: 'Рабочий кабинет без лишнего', text: 'В кабинете преподавателя отображаются только профиль, дисциплины и очередь модерации.' },
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

const dashboardContent = {
  STUDENT: {
    title: 'Ваш кабинет для учёбы и практики',
    lead: 'Здесь доступны тесты, прохождение попыток, статистика и создание собственных материалов.',
    cards: [
      { title: 'Начните с каталога', text: 'Выберите тест из опубликованного списка и откройте его для прохождения.' },
      { title: 'Следите за результатом', text: 'Сравнивайте попытки, смотрите рейтинг и анализируйте слабые темы.' },
      { title: 'Создавайте материалы', text: 'Используйте конструктор тестов, чтобы собрать новый вариант и отправить его на модерацию.' },
    ],
  },
  TEACHER: {
    title: 'Кабинет преподавателя',
    lead: 'В личном кабинете доступны профиль, дисциплины и очередь модерации по закреплённым предметам.',
    cards: [
      { title: 'Проверьте очередь', text: 'Открывайте тесты, отправленные на модерацию, и принимайте решение по публикации.' },
      { title: 'Работайте по дисциплинам', text: 'Система показывает только те материалы, которые относятся к вашим предметам.' },
      { title: 'Сохраняйте качество', text: 'Оценивайте структуру вопросов, корректность ответов и соответствие учебной задаче.' },
    ],
  },
};

const questionDifficultyOptions = [
  { label: 'Лёгкий — 5 points', value: 5 },
  { label: 'Средний — 10 points', value: 10 },
  { label: 'Сложный — 25 points', value: 25 },
];

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

  await Promise.all([loadPublicData(), loadSubjects()]);

  if (state.currentPage === 'dashboard' && !state.token) {
    window.location.href = pageUrls.auth;
    return;
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

  if (state.currentPage === 'dashboard' && state.currentUser?.role === 'STUDENT' && !queryAll('.builder-question').length) {
    addQuestionBlock();
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
      syncRoleSwitch();
      updateRoleUI();
    });
  });
}

function syncRoleSwitch() {
  queryAll('#roleSwitch .role-pill').forEach((pill) => pill.classList.toggle('active', pill.dataset.role === state.currentRole));
}

function updateRoleUI() {
  const isStudent = state.currentRole === 'STUDENT';
  el('studentFields')?.classList.toggle('hidden', !isStudent);
  el('teacherFields')?.classList.toggle('hidden', isStudent);
  if (hasElement('loginRoleHint')) {
    el('loginRoleHint').innerHTML = isStudent
      ? '<strong>Студент:</strong> доступ к тестам, статистике, достижениям и конструктору тестов.'
      : '<strong>Преподаватель:</strong> доступ только к модерации тестов по вашим дисциплинам.';
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
  el('addQuestionBtn')?.addEventListener('click', addQuestionBlock);
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
  const payload = {
    email: el('registerEmail').value,
    password: el('registerPassword').value,
    full_name: el('registerName').value,
    role: state.currentRole,
    faculty: el('registerFaculty').value || null,
    study_group: state.currentRole === 'STUDENT' ? el('registerGroup').value || null : null,
    course: state.currentRole === 'STUDENT' && el('registerCourse').value ? Number(el('registerCourse').value) : null,
    department: state.currentRole === 'TEACHER' ? el('registerDepartment').value || null : null,
    subject_ids: state.currentRole === 'TEACHER' ? getSelectedTeacherSubjectIds() : [],
  };

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
  await ensureSubjectsLoaded();
  const fallbackSubjectIds = state.subjects.slice(0, 2).map((subject) => subject.id);
  try {
    await api('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: 'teacher@skillflow.local',
        password: 'teacher123',
        full_name: 'Demo Teacher',
        role: 'TEACHER',
        faculty: 'Информатика',
        department: 'Кафедра ИТ',
        subject_ids: fallbackSubjectIds,
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
  syncRoleSwitch();
  updateRoleUI();
  updateAuthControls();
  renderProfile();
  renderRoleCapabilities();
  renderDashboardSpotlight();
  toggleRoleWidgets();
  await loadPrivateData();
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
  if (redirect) window.location.href = pageUrls.home;
}

async function ensureSubjectsLoaded() {
  if (!state.subjects.length) await loadSubjects();
}

async function loadSubjects() {
  if (!hasElement('subjectSelect')) return;
  state.subjects = await api('/api/subjects', { headers: {} });
  if (hasElement('subjectSelect')) {
    el('subjectSelect').innerHTML = state.subjects.map((subject) => `<option value="${subject.id}">${subject.name}</option>`).join('');
  }
  if (hasElement('teacherSubjectsSelect')) {
    el('teacherSubjectsSelect').innerHTML = state.subjects.map((subject) => `<option value="${subject.id}">${subject.name}</option>`).join('');
  }
}

function getSelectedTeacherSubjectIds() {
  if (!hasElement('teacherSubjectsSelect')) return [];
  return [...el('teacherSubjectsSelect').selectedOptions].map((option) => Number(option.value));
}

async function loadProfile() {
  if (!state.token) {
    renderProfile();
    return;
  }
  state.currentUser = await api('/api/users/me');
  state.currentRole = state.currentUser.role;
  syncRoleSwitch();
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
  const teachingSubjects = user.teaching_subjects?.length
    ? user.teaching_subjects.map((subject) => subject.name).join(', ')
    : '—';
  el('profileBox').className = 'profile-grid';
  el('profileBox').innerHTML = [
    ['Пользователь', user.full_name],
    ['Email', user.email],
    ['Роль', user.role === 'STUDENT' ? 'Студент' : 'Преподаватель'],
    ['Факультет', user.faculty || '—'],
    ['Группа / курс', user.role === 'STUDENT' ? `${user.study_group || '—'} / ${user.course || '—'}` : '—'],
    ['Кафедра', user.department || '—'],
    ['Дисциплины', teachingSubjects],
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
  queryAll('.student-only').forEach((item) => item.classList.toggle('hidden-by-role', role !== 'STUDENT'));
  queryAll('.teacher-only').forEach((item) => item.classList.toggle('hidden-by-role', role !== 'TEACHER'));
}

async function loadPublicData() {
  const [tests, ratings] = await Promise.all([api('/api/tests', { headers: {} }), api('/api/ratings', { headers: {} })]);
  renderTests(tests);
  renderRatings(ratings);
}

async function loadPrivateData() {
  if (!state.token) return;
  await Promise.all([loadProfile(), loadMyStats(), loadAchievements(), loadMyTests()]);
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
  if (state.currentUser?.role !== 'STUDENT') {
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

function addQuestionBlock() {
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
    <div class="section-title compact-title">
      <div>
        <p class="eyebrow">Вопрос ${index}</p>
        <h3>Параметры вопроса</h3>
      </div>
      <button class="soft-button compact" type="button" data-remove-question>Удалить</button>
    </div>
    <div class="field-row">
      <div class="field-group">
        <label>Сложность</label>
        <select name="points">
          ${questionDifficultyOptions.map((item) => `<option value="${item.value}">${item.label}</option>`).join('')}
        </select>
      </div>
      <div class="field-group">
        <label>Тип вопроса</label>
        <select name="question_type" data-question-type>
          <option value="SINGLE_CHOICE">Одиночный выбор</option>
          <option value="MULTIPLE_CHOICE">Множественный выбор</option>
        </select>
      </div>
    </div>
    <div class="field-group">
      <label>Текст вопроса</label>
      <textarea name="question_text" placeholder="Введите формулировку вопроса" required></textarea>
    </div>
    <div class="answers-block">
      <div class="section-title compact-title">
        <div>
          <p class="eyebrow">Варианты ответа</p>
          <h3>Ответы</h3>
        </div>
        <button class="soft-button compact" type="button" data-add-option>Добавить вариант</button>
      </div>
      <div class="answer-options stack"></div>
    </div>
  `;
  container.appendChild(question);
  question.querySelector('[data-add-option]').addEventListener('click', () => addAnswerOption(question));
  question.querySelector('[data-remove-question]').addEventListener('click', () => removeQuestionBlock(question));
  question.querySelector('[data-question-type]').addEventListener('change', () => syncAnswerInputTypes(question));
  addAnswerOption(question);
  addAnswerOption(question);
  syncAnswerInputTypes(question);
  updateConstructorSummary();
}

function removeQuestionBlock(questionElement) {
  questionElement.remove();
  if (!queryAll('.builder-question').length && hasElement('constructorQuestions')) {
    el('constructorQuestions').className = 'stack empty-state';
    el('constructorQuestions').innerHTML = 'Добавьте первый вопрос, чтобы собрать тест.';
  }
  updateConstructorSummary();
}

function addAnswerOption(questionElement) {
  const answersList = questionElement.querySelector('.answer-options');
  const optionIndex = answersList.children.length + 1;
  const row = document.createElement('div');
  row.className = 'answer-option';
  row.innerHTML = `
    <label class="answer-correct-toggle"></label>
    <input class="answer-text-input" type="text" placeholder="Вариант ответа ${optionIndex}" required />
    <button class="soft-button compact" type="button" data-remove-option>Удалить</button>
  `;
  row.querySelector('[data-remove-option]').addEventListener('click', () => {
    row.remove();
    syncAnswerInputTypes(questionElement);
  });
  answersList.appendChild(row);
  syncAnswerInputTypes(questionElement);
}

function syncAnswerInputTypes(questionElement) {
  const type = questionElement.querySelector('[data-question-type]').value;
  const questionIndex = questionElement.dataset.questionIndex;
  questionElement.querySelectorAll('.answer-option').forEach((row, index) => {
    const toggle = row.querySelector('.answer-correct-toggle');
    toggle.innerHTML = `
      <input type="${type === 'SINGLE_CHOICE' ? 'radio' : 'checkbox'}" name="correct_${questionIndex}" ${index === 0 && type === 'SINGLE_CHOICE' && !questionElement.querySelector(`input[name="correct_${questionIndex}"]:checked`) ? 'checked' : ''} />
      <span>${type === 'SINGLE_CHOICE' ? 'Правильный' : 'Корректный'}</span>
    `;
  });
}

function updateConstructorSummary() {
  if (!hasElement('constructorSummary')) return;
  el('constructorSummary').textContent = `Вопросов: ${queryAll('.builder-question').length}`;
}

function buildConstructorPayload() {
  const questions = queryAll('.builder-question').map((questionElement) => {
    const questionType = questionElement.querySelector('[data-question-type]').value;
    const options = [...questionElement.querySelectorAll('.answer-option')].map((row) => ({
      text: row.querySelector('.answer-text-input').value.trim(),
      is_correct: row.querySelector('input').checked,
    }));
    return {
      text: questionElement.querySelector('[name="question_text"]').value.trim(),
      points: Number(questionElement.querySelector('[name="points"]').value),
      question_type: questionType,
      options,
    };
  });

  if (!questions.length) {
    throw new Error('Добавьте хотя бы один вопрос.');
  }

  questions.forEach((question, index) => {
    if (!question.text) {
      throw new Error(`Заполните текст вопроса №${index + 1}.`);
    }
    if (question.options.length < 2) {
      throw new Error(`У вопроса №${index + 1} должно быть минимум два варианта ответа.`);
    }
    if (question.options.some((option) => !option.text)) {
      throw new Error(`Заполните все варианты ответа у вопроса №${index + 1}.`);
    }
    const correctCount = question.options.filter((option) => option.is_correct).length;
    if (question.question_type === 'SINGLE_CHOICE' && correctCount !== 1) {
      throw new Error(`У вопроса №${index + 1} с одиночным выбором должен быть ровно один правильный ответ.`);
    }
    if (question.question_type === 'MULTIPLE_CHOICE' && correctCount < 1) {
      throw new Error(`У вопроса №${index + 1} с множественным выбором должен быть хотя бы один правильный ответ.`);
    }
  });

  const averagePoints = questions.reduce((sum, question) => sum + question.points, 0) / questions.length;
  const difficulty = averagePoints <= 5 ? 1 : averagePoints <= 10 ? 3 : 5;

  return {
    title: el('testTitleInput').value.trim(),
    description: el('testDescriptionInput').value.trim(),
    subject_id: Number(el('subjectSelect').value),
    difficulty,
    questions,
  };
}

async function createTest(event) {
  event.preventDefault();
  if (!state.token) return;
  try {
    const payload = buildConstructorPayload();
    if (!payload.title) {
      throw new Error('Укажите название теста.');
    }
    const test = await api('/api/tests', { method: 'POST', body: JSON.stringify(payload) });
    el('createMessage').textContent = `Черновик "${test.title}" создан.`;
    event.target.reset();
    resetConstructor();
    await loadMyTests();
  } catch (error) {
    el('createMessage').textContent = error.message;
  }
}

function resetConstructor() {
  state.constructorQuestionCount = 0;
  if (hasElement('constructorQuestions')) {
    el('constructorQuestions').className = 'stack empty-state';
    el('constructorQuestions').innerHTML = 'Добавьте первый вопрос, чтобы собрать тест.';
  }
  updateConstructorSummary();
  addQuestionBlock();
}

async function loadMyTests() {
  if (!state.token) {
    state.myTests = [];
    return;
  }
  state.myTests = await api('/api/tests?mine=true');
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
    : '<div class="empty-state">По вашим дисциплинам нет тестов в очереди модерации.</div>';
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

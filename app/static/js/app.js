const state = {
  token: localStorage.getItem('skillflow_token') || '',
  currentUser: null,
  subjects: [],
  ratings: [],
  selectedTest: null,
  myTests: [],
  currentPage: document.body.dataset.page || 'home',
  currentTheme: localStorage.getItem('skillflow_theme') || 'light',
  currentRole: 'STUDENT',
  currentScreen: 'profile',
  constructorQuestionCount: 0,
  universityCatalog: [],
  telegramLinkTimer: null,
};

const pageUrls = { home: '/', auth: '/auth', dashboard: '/dashboard' };
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
  bindDashboardScreens();
  bindRoleSwitch();
  bindForms();
  bindProfileMenu();
  updateRoleUI();
  updateAuthControls();

  await Promise.all([loadSubjects(), loadUniversityCatalog(), loadPublicData()]);

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
      }
    } catch {
      logout({ redirect: state.currentPage === 'dashboard' });
    }
  }

  if (state.currentPage === 'dashboard' && state.currentUser?.role === 'STUDENT' && !queryAll('.builder-question').length) {
    addQuestionBlock();
  }
}

function bindThemeToggle() {
  el('themeToggleBtn')?.addEventListener('click', () => applyTheme(state.currentTheme === 'light' ? 'dark' : 'light'));
}

function applyTheme(theme) {
  state.currentTheme = theme;
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('skillflow_theme', theme);
}

function bindTabs() {
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

function bindDashboardScreens() {
  queryAll('[data-dashboard-target]').forEach((button) => {
    button.addEventListener('click', () => showDashboardScreen(button.dataset.dashboardTarget));
  });
  if (hasElement('profileBox')) showDashboardScreen(state.currentScreen);
}

function showDashboardScreen(screen) {
  state.currentScreen = screen || 'profile';
  queryAll('[data-dashboard-screen]').forEach((item) => {
    item.classList.toggle('is-hidden', item.dataset.dashboardScreen !== state.currentScreen);
  });
  queryAll('[data-dashboard-target]').forEach((button) => {
    button.classList.toggle('active', button.dataset.dashboardTarget === state.currentScreen);
  });
}

function bindRoleSwitch() {
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
      ? '<strong>Студент:</strong> тесты, рейтинг, результаты и создание тестов.'
      : '<strong>Преподаватель:</strong> модерация тестов и статистика по своим дисциплинам.';
  }
}

function bindProfileMenu() {
  el('profileMenuToggle')?.addEventListener('click', () => el('profileMenuPanel')?.classList.toggle('hidden'));
  document.addEventListener('click', (event) => {
    if (!hasElement('profileMenu') || !hasElement('profileMenuPanel')) return;
    if (!el('profileMenu').contains(event.target)) el('profileMenuPanel').classList.add('hidden');
  });
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
  el('addQuestionBtn')?.addEventListener('click', addQuestionBlock);
  el('ratingSubjectFilter')?.addEventListener('change', renderRatings);
  el('ratingFacultyFilter')?.addEventListener('change', renderRatings);
  el('teacherStatsSubject')?.addEventListener('change', renderTeacherStats);
}

function updateAuthControls() {
  const loggedIn = Boolean(state.token);
  el('authButton')?.classList.toggle('hidden', loggedIn || state.currentPage === 'auth');
  el('homeActionButton')?.classList.toggle('hidden', loggedIn);
  queryAll('.topbar-nav').forEach((nav) => nav.classList.toggle('hidden', loggedIn));
  el('profileMenu')?.classList.toggle('hidden', !loggedIn);
  if (loggedIn && hasElement('profileMenuToggle')) {
    el('profileMenuToggle').textContent = (state.currentUser?.full_name || 'П').trim().charAt(0).toUpperCase();
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
    department: state.currentRole === 'TEACHER' ? getSelectedDepartment() : null,
    program_code: state.currentRole === 'STUDENT' ? getSelectedProgramCode() : null,
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
  toggleRoleWidgets();
  await loadPrivateData();
}

function logout({ redirect = true } = {}) {
  state.token = '';
  state.currentUser = null;
  localStorage.removeItem('skillflow_token');
  updateAuthControls();
  renderProfile();
  renderRoleCapabilities();
  toggleRoleWidgets();
  if (redirect) window.location.href = pageUrls.home;
}

async function loadSubjects() {
  state.subjects = await api('/api/subjects', { headers: {} });
  if (hasElement('subjectSelect')) {
    el('subjectSelect').innerHTML = state.subjects.map((subject) => `<option value="${subject.id}">${subject.name}</option>`).join('');
  }
  if (hasElement('ratingSubjectFilter')) {
    el('ratingSubjectFilter').innerHTML = '<option value="">Все предметы</option>' + state.subjects.map((subject) => `<option value="${subject.name}">${subject.name}</option>`).join('');
  }
  if (hasElement('teacherSubjectsChecklist')) {
    el('teacherSubjectsChecklist').innerHTML = state.subjects.map((subject) => `
      <div class="choice-item"><label><input type="checkbox" value="${subject.id}" data-teacher-subject> ${subject.name}</label></div>
    `).join('');
    queryAll('[data-teacher-subject]').forEach((item) => item.addEventListener('change', renderSelectedTeacherSubjects));
  }
}

async function loadUniversityCatalog() {
  if (!hasElement('registerFaculty') && !hasElement('ratingFacultyFilter')) return;
  state.universityCatalog = await api('/api/university/catalog', { headers: {} });

  if (hasElement('registerFaculty')) {
    el('registerFaculty').innerHTML = state.universityCatalog.map((item) => `<option value="${item.short_name}">${item.short_name}</option>`).join('');
    el('registerFaculty').addEventListener('change', syncInstituteDependentFields);
    syncInstituteDependentFields();
  }

  if (hasElement('ratingFacultyFilter')) {
    el('ratingFacultyFilter').innerHTML = '<option value="">Все институты</option>' + state.universityCatalog.map((item) => `<option value="${item.short_name}">${item.short_name}</option>`).join('');
  }
}

function syncInstituteDependentFields() {
  if (!hasElement('registerFaculty')) return;
  const instituteCode = el('registerFaculty').value;
  const institute = state.universityCatalog.find((item) => item.short_name === instituteCode);

  if (hasElement('registerProgramRadios')) {
    const programs = institute?.programs || [];
    el('registerProgramRadios').innerHTML = programs.length
      ? programs.map((item, index) => `<div class="choice-item"><label><input type="radio" name="programCode" value="${item.code}" ${index === 0 ? 'checked' : ''}> ${item.code} — ${item.name}</label></div>`).join('')
      : '<div class="empty-state">Нет программ</div>';
  }

  if (hasElement('registerDepartmentRadios')) {
    const departments = institute?.departments || [];
    el('registerDepartmentRadios').innerHTML = departments.length
      ? departments.map((item, index) => `<div class="choice-item"><label><input type="radio" name="departmentCode" value="${item.code}" ${index === 0 ? 'checked' : ''}> ${item.code} — ${item.name}</label></div>`).join('')
      : '<div class="empty-state">Нет кафедр</div>';
  }
}

function getSelectedProgramCode() {
  return document.querySelector('input[name="programCode"]:checked')?.value || null;
}

function getSelectedDepartment() {
  return document.querySelector('input[name="departmentCode"]:checked')?.value || null;
}

function getSelectedTeacherSubjectIds() {
  return queryAll('[data-teacher-subject]:checked').map((input) => Number(input.value));
}

function renderSelectedTeacherSubjects() {
  if (!hasElement('teacherSubjectsSelected')) return;
  const selected = queryAll('[data-teacher-subject]:checked').map((input) => input.parentElement.textContent.trim());
  el('teacherSubjectsSelected').textContent = selected.length ? `Выбрано: ${selected.join(', ')}` : 'Ничего не выбрано';
}

async function loadProfile() {
  if (!state.token) return;
  state.currentUser = await api('/api/users/me');
  state.currentRole = state.currentUser.role;
  syncRoleSwitch();
  updateRoleUI();
  updateAuthControls();
  renderProfile();
  renderRoleCapabilities();
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
  return;
  const teachingSubjects = user.teaching_subjects?.length ? user.teaching_subjects.map((s) => s.name).join(', ') : '—';
  el('profileBox').className = 'profile-grid';
  el('profileBox').innerHTML = [
    ['Пользователь', user.full_name],
    ['Email', user.email],
    ['Роль', user.role === 'STUDENT' ? 'Студент' : 'Преподаватель'],
    ['Институт', user.faculty || '—'],
    ['Группа / курс', user.role === 'STUDENT' ? `${user.study_group || '—'} / ${user.course || '—'}` : '—'],
    ['Направление', user.program_code || '—'],
    ['Кафедра', user.department || '—'],
    ['Дисциплины', teachingSubjects],
    ['Telegram', user.telegram_id || 'не привязан'],
  ].map(([label, value]) => `<div><strong>${label}</strong><br>${value}</div>`).join('');
}

function renderRoleCapabilities() {
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

function toggleRoleWidgets() {
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

async function loadPublicData() {
  const [tests, ratings] = await Promise.all([api('/api/tests', { headers: {} }), api('/api/ratings', { headers: {} })]);
  state.ratings = ratings;
  renderRatings();
  renderTests(tests);
  renderStudentRatings();
  renderTeacherStatsFilters();
}

async function loadPrivateData() {
  if (!state.token) return;
  await Promise.all([loadProfile(), loadMyStats(), loadAchievements(), loadMyTests()]);
  if (state.currentUser?.role === 'TEACHER') await loadPendingTests();
}

function getFilteredRatings() {
  const subjectName = el('ratingSubjectFilter')?.value || '';
  const faculty = el('ratingFacultyFilter')?.value || '';
  return state.ratings.filter((item) => (!subjectName || item.subject_name === subjectName) && (!faculty || item.faculty === faculty));
}

function renderRatings() {
  if (!hasElement('ratingsList')) return;
  const ratings = getFilteredRatings();
  el('ratingsList').innerHTML = ratings.length
    ? ratings.map((item) => `
      <div class="list-item">
        <div>
          <strong>#${item.position} ${item.student_name}</strong>
          <p>${item.subject_name} · ${item.faculty || '—'}</p>
        </div>
        <div class="rating-meta"><span>${item.total_score}</span><small>баллов</small></div>
      </div>
    `).join('')
    : '<div class="empty-state">Нет данных по выбранным фильтрам.</div>';
}

function renderStudentRatings() {
  if (!hasElement('studentRatingsList')) return;
  const top = state.ratings.slice(0, 8);
  el('studentRatingsList').innerHTML = top.length
    ? top.map((item) => `<div class="list-item"><strong>#${item.position} ${item.student_name}</strong><p>${item.subject_name}: ${item.total_score}</p></div>`).join('')
    : '<div class="empty-state">Рейтинг появится после первых попыток.</div>';
}

function renderTeacherStatsFilters() {
  if (!hasElement('teacherStatsSubject')) return;
  const names = [...new Set(state.ratings.map((item) => item.subject_name))];
  el('teacherStatsSubject').innerHTML = names.length ? names.map((name) => `<option value="${name}">${name}</option>`).join('') : '<option value="">Нет предметов</option>';
  renderTeacherStats();
}

function renderTeacherStats() {
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

async function loadMyStats() {
  if (!state.token || state.currentUser?.role !== 'STUDENT') return renderStats();
  const stats = await api('/api/stats/me');
  renderStats(stats);
}

function renderStats(stats) {
  if (!hasElement('statsBox')) return;
  if (!stats) {
    el('statsBox').innerHTML = 'После прохождения тестов здесь появится статистика.';
    return;
  }
  const breakdown = Object.entries(stats.subject_breakdown).map(([subject, score]) => `<li>${subject}: ${score}</li>`).join('') || '<li>Пока нет рейтинга</li>';
  const attempts = stats.latest_attempts.map((attempt) => `<li>${attempt.subject_name}: ${attempt.score}/${attempt.max_score}</li>`).join('') || '<li>Нет попыток</li>';
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
  if (!tests.length) return (el('testsList').innerHTML = '<div class="empty-state">Опубликованных тестов пока нет.</div>');
  el('testsList').innerHTML = tests.map((test) => `
    <article class="list-item">
      <strong>${test.title}</strong>
      <p>${test.description || 'Без описания'}</p>
      <p>${test.subject_name} · сложность ${test.difficulty}</p>
      <button class="primary-button compact" type="button" data-open-test="${test.id}">Открыть</button>
    </article>
  `).join('');
  queryAll('[data-open-test]').forEach((button) => button.addEventListener('click', () => openTest(button.dataset.openTest)));
}

async function openTest(testId) {
  if (!state.token) return (window.location.href = pageUrls.auth);
  if (state.currentUser?.role !== 'STUDENT') return;
  const test = await api(`/api/tests/${testId}`);
  state.selectedTest = test;
  const questionsHtml = test.questions.map((question) => `
    <div class="question-block">
      <strong>${question.text}</strong>
      <p>${question.question_type} · ${question.points} баллов</p>
      ${question.options.map((option) => `<label><input type="${question.question_type === 'SINGLE_CHOICE' ? 'radio' : 'checkbox'}" name="q_${question.id}" value="${option.id}"/> ${option.text}</label>`).join('<br>')}
    </div>
  `).join('');
  el('testRunner').innerHTML = `<h3>${test.title}</h3><form id="attemptForm">${questionsHtml}<button class="primary-button" type="submit">Завершить тест</button></form><div id="attemptResult" class="message"></div>`;
  el('attemptForm').addEventListener('submit', submitAttempt);
}

async function submitAttempt(event) {
  event.preventDefault();
  const answers = state.selectedTest.questions.map((question) => ({
    question_id: question.id,
    selected_option_ids: [...event.target.querySelectorAll(`[name="q_${question.id}"]:checked`)].map((input) => Number(input.value))
  }));
  try {
    const result = await api(`/api/tests/${state.selectedTest.id}/attempt`, { method: 'POST', body: JSON.stringify({ answers, allow_retake: false }) });
    el('attemptResult').textContent = `Результат: ${result.score}/${result.max_score} (${result.percentage}%).`;
    await loadPrivateData();
    await loadPublicData();
  } catch (error) {
    el('attemptResult').textContent = error.message;
  }
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
    <div class="section-title compact-title"><div><p class="eyebrow">Вопрос ${index}</p><h3>Параметры вопроса</h3></div><button class="soft-button compact" type="button" data-remove-question>Удалить</button></div>
    <div class="field-row">
      <div class="field-group"><label>Сложность</label><select name="points">${questionDifficultyOptions.map((i) => `<option value="${i.value}">${i.label}</option>`).join('')}</select></div>
      <div class="field-group"><label>Тип вопроса</label><select name="question_type" data-question-type><option value="SINGLE_CHOICE">Одиночный выбор</option><option value="MULTIPLE_CHOICE">Множественный выбор</option></select></div>
    </div>
    <div class="field-group"><label>Текст вопроса</label><textarea name="question_text" required></textarea></div>
    <div class="answers-block"><div class="section-title compact-title"><h3>Ответы</h3><button class="soft-button compact" type="button" data-add-option>Добавить вариант</button></div><div class="answer-options stack"></div></div>
  `;
  container.appendChild(question);
  question.querySelector('[data-add-option]').addEventListener('click', () => addAnswerOption(question));
  question.querySelector('[data-remove-question]').addEventListener('click', () => removeQuestionBlock(question));
  question.querySelector('[data-question-type]').addEventListener('change', () => syncAnswerInputTypes(question));
  addAnswerOption(question); addAnswerOption(question); syncAnswerInputTypes(question); updateConstructorSummary();
}

function removeQuestionBlock(questionElement) {
  questionElement.remove();
  if (!queryAll('.builder-question').length && hasElement('constructorQuestions')) {
    el('constructorQuestions').className = 'stack empty-state';
    el('constructorQuestions').innerHTML = 'Добавьте первый вопрос.';
  }
  updateConstructorSummary();
}

function addAnswerOption(questionElement) {
  const answersList = questionElement.querySelector('.answer-options');
  const optionIndex = answersList.children.length + 1;
  const row = document.createElement('div');
  row.className = 'answer-option';
  row.innerHTML = '<label class="answer-correct-toggle"></label><input class="answer-text-input" type="text" placeholder="Вариант ответа ' + optionIndex + '" required/><button class="soft-button compact" type="button" data-remove-option>Удалить</button>';
  row.querySelector('[data-remove-option]').addEventListener('click', () => { row.remove(); syncAnswerInputTypes(questionElement); });
  answersList.appendChild(row);
  syncAnswerInputTypes(questionElement);
}

function syncAnswerInputTypes(questionElement) {
  const type = questionElement.querySelector('[data-question-type]').value;
  const questionIndex = questionElement.dataset.questionIndex;
  questionElement.querySelectorAll('.answer-option').forEach((row, index) => {
    row.querySelector('.answer-correct-toggle').innerHTML = `<input type="${type === 'SINGLE_CHOICE' ? 'radio' : 'checkbox'}" name="correct_${questionIndex}" ${index === 0 && type === 'SINGLE_CHOICE' ? 'checked' : ''}/><span>${type === 'SINGLE_CHOICE' ? 'Правильный' : 'Корректный'}</span>`;
  });
}

function updateConstructorSummary() {
  if (hasElement('constructorSummary')) el('constructorSummary').textContent = `Вопросов: ${queryAll('.builder-question').length}`;
}

function buildConstructorPayload() {
  const questions = queryAll('.builder-question').map((questionElement) => ({
    text: questionElement.querySelector('[name="question_text"]').value.trim(),
    points: Number(questionElement.querySelector('[name="points"]').value),
    question_type: questionElement.querySelector('[data-question-type]').value,
    options: [...questionElement.querySelectorAll('.answer-option')].map((row) => ({
      text: row.querySelector('.answer-text-input').value.trim(),
      is_correct: row.querySelector('input').checked,
    })),
  }));
  if (!questions.length) throw new Error('Добавьте хотя бы один вопрос.');
  const difficulty = 3;
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
  try {
    const payload = buildConstructorPayload();
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
    el('constructorQuestions').innerHTML = 'Добавьте первый вопрос.';
  }
  updateConstructorSummary();
  addQuestionBlock();
}

async function loadMyTests() {
  if (!state.token) return;
  state.myTests = await api('/api/tests?mine=true');
  renderMyTests();
}

async function submitLatestTest() {
  if (!state.myTests?.length) return (el('createMessage').textContent = 'Сначала создайте тест.');
  const draft = state.myTests.find((item) => item.status === 'DRAFT');
  if (!draft) return (el('createMessage').textContent = 'У вас нет черновиков для отправки.');
  const test = await api(`/api/tests/${draft.id}/submit`, { method: 'POST' });
  el('createMessage').textContent = `Тест "${test.title}" отправлен на модерацию.`;
  await loadMyTests();
}

function renderMyTests() {
  if (!hasElement('myTestsList')) return;
  if (!state.myTests.length) return (el('myTestsList').innerHTML = 'Созданные тесты появятся здесь.');
  el('myTestsList').innerHTML = state.myTests.map((item) => `<article class="list-item"><strong>${item.title}</strong><p>${item.subject_name}</p><p>Статус: ${item.status}</p></article>`).join('');
}

async function loadPendingTests() {
  if (!hasElement('pendingList')) return;
  if (!state.token || state.currentUser?.role !== 'TEACHER') return (el('pendingList').innerHTML = 'Только преподаватель может модерировать тесты.');
  const items = await api('/api/tests/pending');
  el('pendingList').innerHTML = items.length
    ? items.map((item) => `<article class="list-item"><strong>${item.title}</strong><p>${item.author_name} · ${item.subject_name}</p><div class="inline-actions"><button class="primary-button compact" type="button" data-approve="${item.id}">Одобрить</button><button class="soft-button compact" type="button" data-reject="${item.id}">Отклонить</button></div></article>`).join('')
    : '<div class="empty-state">По вашим дисциплинам нет тестов в очереди.</div>';
  queryAll('[data-approve]').forEach((button) => button.addEventListener('click', () => moderate(button.dataset.approve, 'approve')));
  queryAll('[data-reject]').forEach((button) => button.addEventListener('click', () => moderate(button.dataset.reject, 'reject')));
}

async function moderate(testId, action) {
  await api(`/api/tests/${testId}/moderate`, { method: 'POST', body: JSON.stringify({ action, comment: action === 'approve' ? 'Публикуем.' : 'Нужно доработать.' }) });
  await loadPendingTests();
  await loadPublicData();
}

async function linkTelegram() {
  if (!state.token) return;
  const data = await api('/api/telegram/link-code', { method: 'POST' });
  alert(`Код для привязки Telegram: ${data.code}`);
  await loadProfile();
}

function showToast(title, message, durationSeconds = 10) {
  let host = el('toastHost');
  if (!host) {
    host = document.createElement('div');
    host.id = 'toastHost';
    host.className = 'toast-host';
    document.body.appendChild(host);
  }
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.style.setProperty('--toast-duration', `${durationSeconds}s`);
  toast.innerHTML = `<strong>${title}</strong><span>${message}</span>`;
  host.appendChild(toast);
  window.setTimeout(() => toast.remove(), durationSeconds * 1000);
}

function showAchievementToasts(achievements = []) {
  achievements.forEach((achievement) => showToast('Новое достижение', achievement, 10));
}

async function openTest(testId) {
  if (!state.token) return (window.location.href = pageUrls.auth);
  if (state.currentUser?.role !== 'STUDENT') return;
  const test = await api(`/api/tests/${testId}`);
  state.selectedTest = test;
  showDashboardScreen('runner');
  const questionsHtml = test.questions.map((question) => `
    <div class="question-block">
      <strong>${question.text}</strong>
      <p>${question.question_type} · ${question.points} баллов</p>
      ${renderAttemptQuestion(question)}
    </div>
  `).join('');
  el('testRunner').innerHTML = `<h3>${test.title}</h3><form id="attemptForm">${questionsHtml}<button class="primary-button" type="submit">Завершить тест</button></form><div id="attemptResult" class="message"></div>`;
  el('attemptForm').addEventListener('submit', submitAttempt);
}

function renderAttemptQuestion(question) {
  if (question.question_type === 'TEXT_ANSWER') {
    return `<textarea name="q_text_${question.id}" placeholder="Введите ответ"></textarea>`;
  }
  if (question.question_type === 'MATCHING') {
    return question.matching_left.map((left) => `
      <label class="field-group">
        <span>${left}</span>
        <select name="q_match_${question.id}" data-left="${left}">
          <option value="">Выберите пару</option>
          ${question.matching_options.map((right) => `<option value="${right}">${right}</option>`).join('')}
        </select>
      </label>
    `).join('');
  }
  return question.options.map((option) => `<label><input type="${question.question_type === 'SINGLE_CHOICE' ? 'radio' : 'checkbox'}" name="q_${question.id}" value="${option.id}"/> ${option.text}</label>`).join('<br>');
}

async function submitAttempt(event) {
  event.preventDefault();
  const answers = state.selectedTest.questions.map((question) => {
    const answer = { question_id: question.id, selected_option_ids: [] };
    if (question.question_type === 'TEXT_ANSWER') {
      answer.text_answer = event.target.querySelector(`[name="q_text_${question.id}"]`)?.value || '';
    } else if (question.question_type === 'MATCHING') {
      answer.matching_answer = Object.fromEntries(
        [...event.target.querySelectorAll(`[name="q_match_${question.id}"]`)].map((input) => [input.dataset.left, input.value])
      );
    } else {
      answer.selected_option_ids = [...event.target.querySelectorAll(`[name="q_${question.id}"]:checked`)].map((input) => Number(input.value));
    }
    return answer;
  });
  try {
    const result = await api(`/api/tests/${state.selectedTest.id}/attempt`, { method: 'POST', body: JSON.stringify({ answers, allow_retake: false }) });
    el('attemptResult').textContent = `Результат: ${result.score}/${result.max_score} (${result.percentage}%).`;
    showAchievementToasts(result.earned_achievements);
    await loadPrivateData();
    await loadPublicData();
  } catch (error) {
    el('attemptResult').textContent = error.message;
  }
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

function renderAnswerEditor(questionElement) {
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

function addMatchingPair(questionElement) {
  const pairsList = questionElement.querySelector('.matching-pairs');
  const row = document.createElement('div');
  row.className = 'matching-pair';
  row.innerHTML = '<input class="matching-left-input" type="text" placeholder="Левая часть" required/><input class="matching-right-input" type="text" placeholder="Правая часть" required/><button class="soft-button compact" type="button" data-remove-pair>Удалить</button>';
  row.querySelector('[data-remove-pair]').addEventListener('click', () => row.remove());
  pairsList.appendChild(row);
}

function buildConstructorPayload() {
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
    return question;
  });
  if (!questions.length) throw new Error('Добавьте хотя бы один вопрос.');
  return {
    title: el('testTitleInput').value.trim(),
    description: el('testDescriptionInput').value.trim(),
    subject_id: Number(el('subjectSelect').value),
    difficulty: 3,
    questions,
  };
}

async function linkTelegram() {
  if (!state.token) return;
  if (state.telegramLinkTimer) window.clearTimeout(state.telegramLinkTimer);
  const data = await api('/api/telegram/link-code', { method: 'POST' });
  showToast('Telegram link code', `${data.code} · действует ${data.ttl_seconds} сек.`, Math.max(1, data.ttl_seconds));
  state.telegramLinkTimer = window.setTimeout(linkTelegram, Math.max(1, data.ttl_seconds) * 1000);
  await loadProfile();
}

bootstrap();

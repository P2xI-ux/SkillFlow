const state = {
  token: localStorage.getItem('skillflow_token') || '',
  currentUser: null,
  subjects: [],
  selectedTest: null,
  myTests: [],
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

async function bootstrap() {
  bindTabs();
  bindForms();
  await loadSubjects();
  await loadPublicData();
  if (state.token) {
    try {
      await loadProfile();
      await loadPrivateData();
    } catch {
      logout();
    }
  }
}

function bindTabs() {
  document.querySelectorAll('.tab').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach((tab) => tab.classList.remove('active'));
      button.classList.add('active');
      el('loginForm').classList.toggle('hidden', button.dataset.tab !== 'login');
      el('registerForm').classList.toggle('hidden', button.dataset.tab !== 'register');
    });
  });
}

function bindForms() {
  el('loginForm').addEventListener('submit', login);
  el('registerForm').addEventListener('submit', register);
  el('createTestForm').addEventListener('submit', createTest);
  el('refreshTestsBtn').addEventListener('click', loadPublicData);
  el('loadPendingBtn').addEventListener('click', loadPendingTests);
  el('logoutBtn').addEventListener('click', logout);
  el('linkTelegramBtn').addEventListener('click', linkTelegram);
  el('submitLatestTestBtn').addEventListener('click', submitLatestTest);
  el('demoTeacherBtn').addEventListener('click', demoTeacherLogin);
}

async function login(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    const data = await api('/api/auth/login', { method: 'POST', body: JSON.stringify(Object.fromEntries(form)) });
    setSession(data);
  } catch (error) {
    el('authMessage').textContent = error.message;
  }
}

async function register(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = Object.fromEntries(form);
  if (!payload.course) payload.course = null;
  try {
    const data = await api('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });
    setSession(data);
    el('authMessage').textContent = 'Регистрация выполнена.';
  } catch (error) {
    el('authMessage').textContent = error.message;
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
    setSession(data);
  } catch (error) {
    el('authMessage').textContent = error.message;
  }
}

function setSession(data) {
  state.token = data.access_token;
  localStorage.setItem('skillflow_token', state.token);
  state.currentUser = data.user;
  loadProfile();
  loadPrivateData();
}

function logout() {
  state.token = '';
  state.currentUser = null;
  localStorage.removeItem('skillflow_token');
  renderProfile();
  renderStats();
  loadPublicData();
}

async function loadSubjects() {
  state.subjects = await api('/api/subjects', { headers: {} });
  el('subjectSelect').innerHTML = state.subjects.map((subject) => `<option value="${subject.id}">${subject.name}</option>`).join('');
}

async function loadProfile() {
  if (!state.token) return renderProfile();
  state.currentUser = await api('/api/users/me');
  renderProfile();
}

function renderProfile() {
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
    ['Факультет/кафедра', user.faculty || user.department || '—'],
    ['Группа / курс', `${user.study_group || '—'} / ${user.course || '—'}`],
    ['Telegram', user.telegram_id || 'не привязан'],
  ].map(([label, value]) => `<div><strong>${label}</strong><br>${value}</div>`).join('');
}

async function loadPublicData() {
  const [tests, ratings] = await Promise.all([api('/api/tests', { headers: {} }), api('/api/ratings', { headers: {} })]);
  renderTests(tests);
  renderRatings(ratings);
}

async function loadPrivateData() {
  await Promise.all([loadMyStats(), loadAchievements(), loadMyTests()]);
  if (state.currentUser?.role === 'TEACHER') await loadPendingTests();
}

async function loadMyStats() {
  if (!state.token) return renderStats();
  const stats = await api('/api/stats/me');
  renderStats(stats);
}

function renderStats(stats) {
  if (!stats) {
    el('statsBox').className = 'stack empty-state';
    el('statsBox').innerHTML = 'После прохождения тестов здесь появится статистика.';
    return;
  }
  const breakdown = Object.entries(stats.subject_breakdown).map(([subject, score]) => `<li>${subject}: ${score}</li>`).join('') || '<li>Пока нет рейтинга</li>';
  const attempts = stats.latest_attempts.map((attempt) => `<li>${attempt.subject_name}: ${attempt.score}/${attempt.max_score}</li>`).join('') || '<li>Нет попыток</li>';
  el('statsBox').className = 'stack';
  el('statsBox').innerHTML = `
    <div><strong>Пройдено тестов:</strong> ${stats.tests_completed}</div>
    <div><strong>Средний результат:</strong> ${stats.average_score_percent}%</div>
    <div><strong>Суммарный рейтинг:</strong> ${stats.rating_total}</div>
    <div><strong>Баллы по предметам:</strong><ul>${breakdown}</ul></div>
    <div><strong>Последние попытки:</strong><ul>${attempts}</ul></div>
  `;
}

async function loadAchievements() {
  if (!state.token) return (el('achievementsList').innerHTML = '');
  const items = await api('/api/achievements/me');
  el('achievementsList').innerHTML = items.length
    ? items.map((item) => `<div class="list-item"><strong>${item.name}</strong><p>${item.description}</p></div>`).join('')
    : '<div class="empty-state">Достижения ещё не открыты.</div>';
}

function renderTests(tests) {
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
      <button data-open-test="${test.id}">Открыть</button>
    </article>
  `).join('');
  list.querySelectorAll('[data-open-test]').forEach((button) => button.addEventListener('click', () => openTest(button.dataset.openTest)));
}

async function openTest(testId) {
  if (!state.token) {
    el('testRunner').innerHTML = 'Сначала выполните вход.';
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
    <form id="attemptForm">${questionsHtml}<button type="submit">Завершить тест</button></form>
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
  if (!state.token) return;
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
          <button data-approve="${item.id}">Одобрить</button>
          <button class="secondary" data-reject="${item.id}">Отклонить</button>
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
  el('ratingsList').innerHTML = ratings.length
    ? ratings.map((item) => `<div class="list-item">#${item.position} ${item.student_name} — ${item.total_score} (${item.subject_name})</div>`).join('')
    : '<div class="empty-state">Рейтинг появится после первых прохождений.</div>';
}

async function linkTelegram() {
  if (!state.token) return;
  const data = await api('/api/telegram/link-code', { method: 'POST' });
  alert(`Код для привязки Telegram: ${data.code}`);
  await loadProfile();
}

bootstrap();

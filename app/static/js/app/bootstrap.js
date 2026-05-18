import { state } from '../core/state.js';
import { el, hasElement, queryAll } from '../core/dom.js';
import { pageUrls } from '../shared/constants.js';
import { applyTheme, bindThemeToggle } from '../features/theme/theme.js';
import { bindTabs, bindRoleSwitch, syncRoleSwitch, updateAuthControls, updateRoleUI } from '../features/auth/auth.ui.js';
import { login, logout, register } from '../features/auth/auth.handlers.js';
import { fetchMyAchievements, fetchMyProfile, fetchMyStats, fetchSubjects, fetchUniversityCatalog } from '../features/profile/profile.api.js';
import { renderAchievements, renderProfile, renderRoleCapabilities, renderStats, showDashboardScreen, toggleRoleWidgets } from '../features/profile/profile.ui.js';
import { fetchRatings } from '../features/rating/rating.api.js';
import { renderRatings, renderStudentRatings, renderTeacherStats, renderTeacherStatsFilters } from '../features/rating/rating.ui.js';
import { addQuestionBlock, resetConstructor } from '../features/constructor/constructor.ui.js';
import { buildConstructorPayload } from '../features/constructor/constructor.payload.js';
import { fetchMyTests, fetchTests, createTestApi, submitTestApi } from '../features/tests/tests.api.js';
import { openTest, renderMyTests, renderTests } from '../features/tests/test-runner.ui.js';
import { submitAttempt } from '../features/tests/test-attempt.handlers.js';
import { loadPendingTests } from '../features/moderation/moderation.ui.js';
import { moderateTest } from '../features/moderation/moderation.api.js';
import { requestTelegramLinkCode } from '../features/telegram/telegram.api.js';
import { showAchievementToasts, showTelegramCodeModal, showToast } from '../features/telegram/telegram.ui.js';

function hooks() {
  return { renderProfile, renderRoleCapabilities, toggleRoleWidgets, loadPrivateData };
}

async function loadProfile() {
  if (!state.token) return;
  state.currentUser = await fetchMyProfile();
  state.currentRole = state.currentUser.role;
  syncRoleSwitch();
  updateRoleUI();
  updateAuthControls();
  renderProfile();
  renderRoleCapabilities();
  toggleRoleWidgets();
}

async function loadSubjectsData() {
  state.subjects = await fetchSubjects();
  if (hasElement('subjectSelect')) {
    el('subjectSelect').innerHTML = state.subjects.map((subject) => `<option value="${subject.id}">${subject.name}</option>`).join('');
  }
  if (hasElement('ratingSubjectFilter')) {
    el('ratingSubjectFilter').innerHTML =
      '<option value="">Все предметы</option>' + state.subjects.map((subject) => `<option value="${subject.name}">${subject.name}</option>`).join('');
  }
  if (hasElement('teacherSubjectsChecklist')) {
    el('teacherSubjectsChecklist').innerHTML = state.subjects
      .map((subject) => `<div class="choice-item"><label><input type="checkbox" value="${subject.id}" data-teacher-subject> ${subject.name}</label></div>`)
      .join('');
    queryAll('[data-teacher-subject]').forEach((item) => item.addEventListener('change', renderSelectedTeacherSubjects));
  }
}

function syncInstituteDependentFields() {
  if (!hasElement('registerFaculty')) return;
  const instituteCode = el('registerFaculty').value;
  const institute = state.universityCatalog.find((item) => item.short_name === instituteCode);

  if (hasElement('registerProgramRadios')) {
    const programs = institute?.programs || [];
    el('registerProgramRadios').innerHTML = programs.length
      ? programs
          .map(
            (item, index) =>
              `<div class="choice-item"><label><input type="radio" name="programCode" value="${item.code}" ${index === 0 ? 'checked' : ''}> ${item.code} — ${item.name}</label></div>`,
          )
          .join('')
      : '<div class="empty-state">Нет программ</div>';
  }

  if (hasElement('registerDepartmentRadios')) {
    const departments = institute?.departments || [];
    el('registerDepartmentRadios').innerHTML = departments.length
      ? departments
          .map(
            (item, index) =>
              `<div class="choice-item"><label><input type="radio" name="departmentCode" value="${item.code}" ${index === 0 ? 'checked' : ''}> ${item.code} — ${item.name}</label></div>`,
          )
          .join('')
      : '<div class="empty-state">Нет кафедр</div>';
  }
}

function renderSelectedTeacherSubjects() {
  if (!hasElement('teacherSubjectsSelected')) return;
  const selected = queryAll('[data-teacher-subject]:checked').map((input) => input.parentElement.textContent.trim());
  el('teacherSubjectsSelected').textContent = selected.length ? `Выбрано: ${selected.join(', ')}` : 'Ничего не выбрано';
}

async function loadUniversityCatalogData() {
  if (!hasElement('registerFaculty') && !hasElement('ratingFacultyFilter')) return;
  state.universityCatalog = await fetchUniversityCatalog();

  if (hasElement('registerFaculty')) {
    el('registerFaculty').innerHTML = state.universityCatalog.map((item) => `<option value="${item.short_name}">${item.short_name}</option>`).join('');
    el('registerFaculty').addEventListener('change', syncInstituteDependentFields);
    syncInstituteDependentFields();
  }

  if (hasElement('ratingFacultyFilter')) {
    el('ratingFacultyFilter').innerHTML =
      '<option value="">Все институты</option>' + state.universityCatalog.map((item) => `<option value="${item.short_name}">${item.short_name}</option>`).join('');
  }
}

async function loadPublicData() {
  const [tests, ratings] = await Promise.all([fetchTests(), fetchRatings()]);
  state.ratings = ratings;
  renderRatings();
  renderTests(tests, (testId, allowRetake) =>
    openTest(testId, (event) => submitAttempt(event, { showAchievementToasts, loadPrivateData, loadPublicData }), showDashboardScreen, allowRetake),
  );
  renderStudentRatings();
  renderTeacherStatsFilters();
}

async function loadMyStats() {
  if (!state.token || state.currentUser?.role !== 'STUDENT') return renderStats();
  const stats = await fetchMyStats();
  renderStats(stats);
}

async function loadAchievements() {
  if (!hasElement('achievementsList')) return;
  if (!state.token || state.currentUser?.role !== 'STUDENT') return renderAchievements([]);
  const items = await fetchMyAchievements();
  renderAchievements(items);
}

async function loadMyTests() {
  if (!state.token) return;
  state.myTests = await fetchMyTests();
  renderMyTests();
}

async function loadPrivateData() {
  if (!state.token) return;
  await Promise.all([loadProfile(), loadMyStats(), loadAchievements(), loadMyTests()]);
  if (state.currentUser?.role === 'TEACHER') await loadPendingTests(moderate);
}

async function moderate(testId, action) {
  await moderateTest(testId, action);
  await loadPendingTests(moderate);
  await loadPublicData();
}

async function createTest(event) {
  event.preventDefault();
  try {
    const payload = buildConstructorPayload();
    const test = await createTestApi(payload);
    el('createMessage').textContent = `Черновик "${test.title}" создан.`;
    event.target.reset();
    resetConstructor();
    await loadMyTests();
  } catch (error) {
    el('createMessage').textContent = error.message;
  }
}

async function submitLatestTest() {
  if (!state.myTests?.length) return (el('createMessage').textContent = 'Сначала создайте тест.');
  const draft = state.myTests.find((item) => item.status === 'DRAFT');
  if (!draft) return (el('createMessage').textContent = 'У вас нет черновиков для отправки.');
  const test = await submitTestApi(draft.id);
  el('createMessage').textContent = `Тест "${test.title}" отправлен на модерацию.`;
  await loadMyTests();
}

async function linkTelegram() {
  if (!state.token) return;
  if (state.telegramLinkTimer) window.clearTimeout(state.telegramLinkTimer);
  const data = await requestTelegramLinkCode();
  showTelegramCodeModal(data.code, Math.max(1, data.ttl_seconds));
  showToast('Telegram', 'Код отображён в отдельном окне.', 5);
  state.telegramLinkTimer = window.setTimeout(linkTelegram, Math.max(1, data.ttl_seconds) * 1000);
  await loadProfile();
}

function bindDashboardScreens() {
  queryAll('[data-dashboard-target]').forEach((button) => {
    button.addEventListener('click', () => showDashboardScreen(button.dataset.dashboardTarget));
  });
  if (hasElement('profileBox')) showDashboardScreen(state.currentScreen);
}

function bindProfileMenu() {
  el('profileMenuToggle')?.addEventListener('click', () => el('profileMenuPanel')?.classList.toggle('hidden'));
  document.addEventListener('click', (event) => {
    if (!hasElement('profileMenu') || !hasElement('profileMenuPanel')) return;
    if (!el('profileMenu').contains(event.target)) el('profileMenuPanel').classList.add('hidden');
  });
}

function bindForms() {
  el('loginForm')?.addEventListener('submit', (event) => login(event, hooks()));
  el('registerForm')?.addEventListener('submit', (event) => register(event, hooks()));
  el('createTestForm')?.addEventListener('submit', createTest);
  el('refreshTestsBtn')?.addEventListener('click', loadPublicData);
  el('loadPendingBtn')?.addEventListener('click', () => loadPendingTests(moderate));
  el('logoutBtn')?.addEventListener('click', () => logout({ redirect: true }, hooks()));
  el('linkTelegramBtn')?.addEventListener('click', linkTelegram);
  el('submitLatestTestBtn')?.addEventListener('click', submitLatestTest);
  el('addQuestionBtn')?.addEventListener('click', addQuestionBlock);
  el('ratingSubjectFilter')?.addEventListener('change', renderRatings);
  el('ratingFacultyFilter')?.addEventListener('change', renderRatings);
  el('teacherStatsSubject')?.addEventListener('change', renderTeacherStats);
}

export async function bootstrap() {
  applyTheme(state.currentTheme);
  bindThemeToggle();
  bindTabs();
  bindDashboardScreens();
  bindRoleSwitch();
  bindForms();
  bindProfileMenu();
  updateRoleUI();
  updateAuthControls();

  await Promise.all([loadSubjectsData(), loadUniversityCatalogData(), loadPublicData()]);

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
      logout({ redirect: state.currentPage === 'dashboard' }, hooks());
    }
  }

  if (state.currentPage === 'dashboard' && state.currentUser?.role === 'STUDENT' && !queryAll('.builder-question').length) {
    addQuestionBlock();
  }
}

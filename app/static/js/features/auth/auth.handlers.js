import { state } from '../../core/state.js';
import { storage } from '../../core/storage.js';
import { el, hasElement, queryAll } from '../../core/dom.js';
import { pageUrls } from '../../shared/constants.js';
import { loginApi, registerApi } from './auth.api.js';
import { syncRoleSwitch, updateRoleUI, updateAuthControls } from './auth.ui.js';
import { setBusy } from '../../core/ui.js';

export async function setSession(data, hooks) {
  state.token = data.access_token;
  storage.setToken(state.token);
  state.currentUser = data.user;
  state.currentRole = data.user.role;
  syncRoleSwitch();
  updateRoleUI();
  updateAuthControls();
  hooks.renderProfile();
  hooks.renderRoleCapabilities();
  hooks.toggleRoleWidgets();
  await hooks.loadPrivateData();
}

export function logout({ redirect = true } = {}, hooks) {
  state.token = '';
  state.currentUser = null;
  storage.clearToken();
  updateAuthControls();
  hooks.renderProfile();
  hooks.renderRoleCapabilities();
  hooks.toggleRoleWidgets();
  if (redirect) window.location.href = pageUrls.home;
}

export async function login(event, hooks) {
  event.preventDefault();
  const form = new FormData(event.target);
  const submitButton = event.submitter || event.target.querySelector('button[type="submit"]');
  setBusy(submitButton, true, 'Входим...');
  try {
    const data = await loginApi(Object.fromEntries(form));
    await setSession(data, hooks);
    if (hasElement('authMessage')) el('authMessage').textContent = 'Вход выполнен успешно.';
    window.location.href = pageUrls.dashboard;
  } catch (error) {
    if (hasElement('authMessage')) el('authMessage').textContent = error.message;
  } finally {
    setBusy(submitButton, false);
  }
}

export async function register(event, hooks) {
  event.preventDefault();
  const submitButton = event.submitter || event.target.querySelector('button[type="submit"]');
  setBusy(submitButton, true, 'Создаём...');
  const payload = {
    email: el('registerEmail').value,
    password: el('registerPassword').value,
    full_name: el('registerName').value,
    role: state.currentRole,
    faculty_id: el('registerFaculty').value ? Number(el('registerFaculty').value) : null,
    study_group: state.currentRole === 'STUDENT' ? el('registerGroup').value || null : null,
    admission_year: state.currentRole === 'STUDENT' && el('registerAdmissionYear').value ? Number(el('registerAdmissionYear').value) : null,
    department_id: state.currentRole === 'TEACHER' ? Number(document.querySelector('input[name="departmentId"]:checked')?.value) || null : null,
    program_id: state.currentRole === 'STUDENT' ? Number(document.querySelector('input[name="programId"]:checked')?.value) || null : null,
    subject_ids: queryAll('[data-teacher-subject]:checked').map((input) => Number(input.value)),
  };

  try {
    const data = await registerApi(payload);
    await setSession(data, hooks);
    if (hasElement('authMessage')) el('authMessage').textContent = 'Регистрация выполнена.';
    window.location.href = pageUrls.dashboard;
  } catch (error) {
    if (hasElement('authMessage')) el('authMessage').textContent = error.message;
  } finally {
    setBusy(submitButton, false);
  }
}

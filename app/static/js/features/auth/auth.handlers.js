import { state } from '../../core/state.js';
import { storage } from '../../core/storage.js';
import { el, hasElement, queryAll } from '../../core/dom.js';
import { pageUrls } from '../../shared/constants.js';
import { loginApi, registerApi } from './auth.api.js';
import { syncRoleSwitch, updateRoleUI, updateAuthControls } from './auth.ui.js';

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
  try {
    const data = await loginApi(Object.fromEntries(form));
    await setSession(data, hooks);
    if (hasElement('authMessage')) el('authMessage').textContent = 'Вход выполнен успешно.';
    window.location.href = pageUrls.dashboard;
  } catch (error) {
    if (hasElement('authMessage')) el('authMessage').textContent = error.message;
  }
}

export async function register(event, hooks) {
  event.preventDefault();
  const payload = {
    email: el('registerEmail').value,
    password: el('registerPassword').value,
    full_name: el('registerName').value,
    role: state.currentRole,
    faculty: el('registerFaculty').value || null,
    study_group: state.currentRole === 'STUDENT' ? el('registerGroup').value || null : null,
    course: state.currentRole === 'STUDENT' && el('registerCourse').value ? Number(el('registerCourse').value) : null,
    department: state.currentRole === 'TEACHER' ? document.querySelector('input[name="departmentCode"]:checked')?.value || null : null,
    program_code: state.currentRole === 'STUDENT' ? document.querySelector('input[name="programCode"]:checked')?.value || null : null,
    subject_ids: queryAll('[data-teacher-subject]:checked').map((input) => Number(input.value)),
  };

  try {
    const data = await registerApi(payload);
    await setSession(data, hooks);
    if (hasElement('authMessage')) el('authMessage').textContent = 'Регистрация выполнена.';
    window.location.href = pageUrls.dashboard;
  } catch (error) {
    if (hasElement('authMessage')) el('authMessage').textContent = error.message;
  }
}

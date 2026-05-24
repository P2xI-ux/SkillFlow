import { state } from '../../core/state.js';
import { el, hasElement, queryAll } from '../../core/dom.js';

export function syncRoleSwitch() {
  queryAll('#roleSwitch .role-pill').forEach((pill) => pill.classList.toggle('active', pill.dataset.role === state.currentRole));
}

export function updateRoleUI() {
  const isStudent = state.currentRole === 'STUDENT';
  el('studentFields')?.classList.toggle('hidden', !isStudent);
  el('teacherFields')?.classList.toggle('hidden', isStudent);
  if (hasElement('loginRoleHint')) {
    el('loginRoleHint').innerHTML = isStudent
      ? '<strong>Студент:</strong> тесты, рейтинг, результаты и создание тестов.'
      : '<strong>Преподаватель:</strong> модерация тестов и статистика по своим дисциплинам.';
  }
}

export function updateAuthControls() {
  const loggedIn = Boolean(state.token);
  el('authButton')?.classList.toggle('hidden', loggedIn || state.currentPage === 'auth');
  el('homeActionButton')?.classList.toggle('hidden', loggedIn);
  el('profileMenu')?.classList.toggle('hidden', !loggedIn);
  if (loggedIn && hasElement('profileMenuToggle')) {
    el('profileMenuToggle').textContent = (state.currentUser?.full_name || 'П').trim().charAt(0).toUpperCase();
  }
}

export function bindTabs() {
  queryAll('.tab[data-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      queryAll('.tab[data-tab]').forEach((tab) => tab.classList.remove('active'));
      button.classList.add('active');
      el('loginForm')?.classList.toggle('hidden', button.dataset.tab !== 'login');
      el('registerForm')?.classList.toggle('hidden', button.dataset.tab !== 'register');
      if (hasElement('authMessage')) el('authMessage').textContent = '';
    });
  });
}

export function bindRoleSwitch() {
  queryAll('#roleSwitch .role-pill').forEach((button) => {
    button.addEventListener('click', () => {
      state.currentRole = button.dataset.role;
      syncRoleSwitch();
      updateRoleUI();
    });
  });
}

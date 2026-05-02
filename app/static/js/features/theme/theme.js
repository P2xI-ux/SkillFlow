import { state } from '../../core/state.js';
import { el } from '../../core/dom.js';
import { storage } from '../../core/storage.js';

export function applyTheme(theme) {
  state.currentTheme = theme;
  document.documentElement.dataset.theme = theme;
  storage.setTheme(theme);
}

export function bindThemeToggle() {
  el('themeToggleBtn')?.addEventListener('click', () => applyTheme(state.currentTheme === 'light' ? 'dark' : 'light'));
}

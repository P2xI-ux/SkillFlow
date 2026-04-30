import { el } from '../../core/dom.js';

export function showToast(title, message, durationSeconds = 10) {
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

export function showAchievementToasts(achievements = []) {
  achievements.forEach((achievement) => showToast('Новое достижение', achievement, 10));
}

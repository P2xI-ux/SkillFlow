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

export function showTelegramCodeModal(code, ttlSeconds) {
  let overlay = el('telegramCodeModalOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'telegramCodeModalOverlay';
    overlay.className = 'telegram-code-modal-overlay';
    overlay.innerHTML = `
      <div class="telegram-code-modal" role="dialog" aria-modal="true" aria-labelledby="telegramCodeTitle">
        <button id="telegramCodeModalClose" class="soft-button compact" type="button">Закрыть</button>
        <h3 id="telegramCodeTitle">Код привязки Telegram</h3>
        <p id="telegramCodeValue" class="telegram-code-value"></p>
        <p id="telegramCodeTtl" class="helper-text"></p>
      </div>
    `;
    document.body.appendChild(overlay);
    const close = () => overlay.classList.add('hidden');
    el('telegramCodeModalClose')?.addEventListener('click', close);
    overlay.addEventListener('click', (event) => {
      if (event.target === overlay) close();
    });
  }
  el('telegramCodeValue').textContent = code;
  el('telegramCodeTtl').textContent = `Код действует ${ttlSeconds} сек.`;
  overlay.classList.remove('hidden');
}

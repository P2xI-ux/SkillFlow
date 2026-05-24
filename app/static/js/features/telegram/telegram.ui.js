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

let countdownInterval = null;

export function showTelegramCodeModal(code, ttlSeconds, onClose = null) {
  let overlay = el('telegramCodeModalOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'telegramCodeModalOverlay';
    overlay.className = 'telegram-code-modal-overlay hidden';
    document.body.appendChild(overlay);
  }

  if (countdownInterval) {
    clearInterval(countdownInterval);
  }

  overlay.innerHTML = `
    <div class="telegram-code-modal" role="dialog" aria-modal="true" aria-labelledby="telegramCodeTitle" style="position: relative; max-width: 400px; width: 100%; padding: 28px; text-align: center; border-radius: 20px; box-shadow: 0 16px 48px var(--glass-shadow); border: 1px solid var(--glass-border); background: var(--glass-bg); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);">
      <button id="telegramCodeModalClose" class="soft-button compact" type="button" style="position: absolute; top: 16px; right: 16px; width: 32px; height: 32px; border-radius: 50%; padding: 0; display: grid; place-items: center; border: 1px solid var(--line); font-size: 1.25rem; font-weight: 300;">&times;</button>

      <div style="margin-bottom: 16px; margin-top: 10px;">
        <span class="eyebrow" style="color: var(--primary-2); font-size: 0.75rem;">Интеграция</span>
        <h3 id="telegramCodeTitle" style="margin-top: 6px; margin-bottom: 8px;">Привязка к Telegram</h3>
        <p style="font-size: 0.88rem; color: var(--muted); line-height: 1.4; margin-bottom: 0;">
          Откройте <a href="https://t.me/YmeniePotokBot" target="_blank" style="color: var(--primary); text-decoration: underline; font-weight: 500;">@YmeniePotokBot</a> и отправьте команду привязки с этим кодом:
        </p>
      </div>

      <div style="margin: 20px 0; background: var(--surface-2); padding: 16px; border-radius: 16px; border: 1px solid var(--line);">
        <code style="font-family: monospace; font-size: 0.95rem; display: block; margin-bottom: 12px; color: var(--muted); background: var(--surface); padding: 6px 12px; border-radius: 8px; border: 1px solid var(--line);">/link ${code}</code>
        <div id="telegramCodeDigits" style="display: flex; gap: 8px; justify-content: center; margin: 12px 0;">
          ${String(code)
            .split('')
            .map(
              (digit) => `
            <span style="
              display: inline-flex;
              align-items: center;
              justify-content: center;
              width: 38px;
              height: 46px;
              font-size: 1.6rem;
              font-weight: 700;
              background: var(--surface);
              border: 1px solid var(--line);
              border-radius: 10px;
              color: var(--text);
            ">${digit}</span>
          `,
            )
            .join('')}
        </div>
      </div>

      <div style="display: flex; align-items: center; justify-content: center; gap: 6px; margin-top: 16px; font-size: 0.85rem; color: var(--muted);">
        <svg class="icon" viewBox="0 0 24 24" style="width: 16px; height: 16px; color: var(--primary); stroke: currentColor; stroke-width: 2; fill: none;"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round"/></svg>
        <span id="telegramCodeTtl">Действует ${ttlSeconds} сек.</span>
      </div>

      <div style="margin-top: 12px; height: 4px; background: var(--line); border-radius: 2px; overflow: hidden;">
        <div id="telegramCodeProgressBar" style="height: 100%; width: 100%; background: var(--primary); transition: width 0.2s linear;"></div>
      </div>
    </div>
  `;

  const close = () => {
    overlay.classList.add('hidden');
    if (countdownInterval) {
      clearInterval(countdownInterval);
      countdownInterval = null;
    }
    if (onClose) onClose();
  };

  el('telegramCodeModalClose').onclick = close;
  overlay.onclick = (event) => {
    if (event.target === overlay) close();
  };

  let timeLeft = ttlSeconds;
  const updateTimer = () => {
    if (timeLeft <= 0) {
      clearInterval(countdownInterval);
      countdownInterval = null;
      return;
    }
    el('telegramCodeTtl').textContent = `Код действует ${timeLeft} сек.`;
    const percent = (timeLeft / ttlSeconds) * 100;
    const bar = el('telegramCodeProgressBar');
    if (bar) bar.style.width = `${percent}%`;
    timeLeft--;
  };

  updateTimer();
  countdownInterval = setInterval(updateTimer, 1000);
  overlay.classList.remove('hidden');
}

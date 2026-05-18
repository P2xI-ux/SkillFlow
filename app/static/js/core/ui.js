export function setBusy(control, isBusy, busyText = 'Подождите...') {
  if (!control) return;
  if (isBusy) {
    control.dataset.originalText = control.textContent;
    control.textContent = busyText;
    control.disabled = true;
    control.setAttribute('aria-busy', 'true');
    return;
  }
  control.textContent = control.dataset.originalText || control.textContent;
  control.disabled = false;
  control.removeAttribute('aria-busy');
  delete control.dataset.originalText;
}

export function formatApiError(error) {
  if (!error) return 'Ошибка запроса';
  if (typeof error === 'string') return error;
  if (Array.isArray(error)) {
    return error.map((item) => item.msg || item.message || String(item)).join('; ');
  }
  if (typeof error === 'object') {
    return error.msg || error.message || JSON.stringify(error);
  }
  return String(error);
}

export const storage = {
  getToken: () => localStorage.getItem('skillflow_token') || '',
  setToken: (token) => localStorage.setItem('skillflow_token', token),
  clearToken: () => localStorage.removeItem('skillflow_token'),
  getTheme: () => localStorage.getItem('skillflow_theme') || 'light',
  setTheme: (theme) => localStorage.setItem('skillflow_theme', theme),
};

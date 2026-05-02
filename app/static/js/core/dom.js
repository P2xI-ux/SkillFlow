export const el = (id) => document.getElementById(id);
export const queryAll = (selector) => [...document.querySelectorAll(selector)];
export const hasElement = (id) => Boolean(el(id));

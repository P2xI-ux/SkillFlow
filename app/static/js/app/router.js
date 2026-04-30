import { pageUrls } from '../shared/constants.js';

export function goTo(page) {
  if (pageUrls[page]) window.location.href = pageUrls[page];
}

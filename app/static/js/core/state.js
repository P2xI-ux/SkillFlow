import { storage } from './storage.js';

export const state = {
  token: storage.getToken(),
  currentUser: null,
  subjects: [],
  ratings: [],
  selectedTest: null,
  selectedTestAllowRetake: false,
  myTests: [],
  currentPage: document.body.dataset.page || 'home',
  currentTheme: storage.getTheme(),
  currentRole: 'STUDENT',
  currentScreen: 'profile',
  constructorQuestionCount: 0,
  universityCatalog: [],
  telegramLinkTimer: null,
};

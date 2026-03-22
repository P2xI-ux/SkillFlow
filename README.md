# SkillFlow MVP

SkillFlow MVP — это рабочий прототип по ТЗ из репозитория: веб-приложение на FastAPI с адаптивным frontend, REST API, модерацией тестов, рейтингом, достижениями и Telegram-ботом на aiogram.

## Что реализовано

- регистрация и вход для студента и преподавателя;
- создание тестов со статусами `DRAFT -> PENDING_MODERATION -> PUBLISHED` через state machine;
- модерация тестов преподавателем;
- прохождение опубликованных тестов с подсчётом результата;
- observer-поток после завершения теста: обновление рейтинга и выдача достижений;
- стратегия расчёта рейтинговых баллов по сложности теста;
- factory method для построения single/multiple choice вопросов;
- Telegram adapter + bot-команды `/start`, `/tests`, `/rating`, `/stats`, `/link`, `/token`;
- Swagger-документация по адресу `http://localhost:8000/docs`.

## Архитектура

```text
app/
  api/           HTTP-маршруты FastAPI
  core/          конфигурация, БД, безопасность
  models/        SQLAlchemy-сущности и enum'ы
  repositories/  слой Repository
  services/      state machine, observer, strategy, factory, adapter
  static/        frontend (HTML/CSS/JS)
bot/             aiogram-бот
```

Дополнительно добавлен файл `ARCHITECTURE.md` и пакет `app/modules/`, чтобы структура проекта напрямую читалась в терминах диаграммы классов: `users`, `content`, `execution`, `gamification`, `integration`, `data_access`.

## Быстрый запуск локально

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

После старта:
- веб: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`
- healthcheck: `http://localhost:8000/health`

## Docker Compose

```bash
docker compose up --build
```

Сервис `app` поднимает веб-приложение и API. Сервис `bot` стартует только если передан `TELEGRAM_BOT_TOKEN`.

## Пример пользовательского сценария MVP

1. Зарегистрируйте студента через форму или API.
2. Создайте тест в блоке «Создание теста».
3. Нажмите «Отправить последний мой тест на модерацию».
4. Войдите как преподаватель кнопкой demo login и одобрите тест.
5. Вернитесь под студентом, откройте тест из каталога и завершите его.
6. Проверьте рейтинг, статистику и достижения.
7. Для Telegram привязки получите код в профиле и отправьте боту `/link 123456`.

## Тесты

```bash
pytest
```

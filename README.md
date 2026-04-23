# SkillFlow MVP

SkillFlow MVP — прототип обучающей платформы для создания, модерации и прохождения тестов.

Технологический стек:
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Frontend:** HTML/CSS/JavaScript (адаптивный интерфейс)
- **Интеграции:** Telegram-бот на aiogram

## Функциональность

### Управление пользователями
- регистрация и авторизация;
- роли: студент и преподаватель;
- демо-вход для ускоренной проверки сценариев.

### Жизненный цикл тестов
- создание тестов и вопросов;
- перевод теста по статусам `DRAFT -> PENDING_MODERATION -> PUBLISHED`;
- модерация преподавателем;
- публикация после одобрения.

### Прохождение и аналитика
- прохождение опубликованных тестов;
- автоматический подсчет результата;
- обновление рейтинга после завершения теста;
- выдача достижений;
- просмотр статистики и лидерборда.

### Telegram-интеграция
Поддерживаются команды:
- `/start`
- `/tests`
- `/rating`
- `/stats`
- `/link`
- `/token`

## Архитектура проекта

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

Дополнительно:
- `ARCHITECTURE.md` — архитектурные решения и декомпозиция;
- `app/modules/` — структурирование доменов (`users`, `content`, `execution`, `gamification`, `integration`, `data_access`).

## Запуск локально

### 1) Подготовка окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Старт приложения

```bash
uvicorn app.main:app --reload
```

После запуска доступны:
- `http://localhost:8000/` — веб-интерфейс;
- `http://localhost:8000/docs` — Swagger/OpenAPI;
- `http://localhost:8000/health` — healthcheck.

## Запуск через Docker Compose

```bash
docker compose up --build
```

Сервисы:
- `app` — web + REST API;
- `bot` — Telegram-бот (запускается с заданным `TELEGRAM_BOT_TOKEN`).

Базовые переменные окружения:
- `DATABASE_URL` (по умолчанию `sqlite:///./skillflow.db`)
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `APP_BASE_URL`
- `API_BASE_URL`
- `TELEGRAM_BOT_TOKEN`

## Демонстрационный сценарий

1. Зарегистрировать пользователя-студента.
2. Создать тест в интерфейсе.
3. Отправить тест на модерацию.
4. Войти как преподаватель и одобрить тест.
5. Вернуться в роль студента и пройти опубликованный тест.
6. Проверить изменения в рейтинге, статистике и достижениях.
7. Для Telegram-связки получить код и выполнить `/link <код>` в боте.

## Тестирование

```bash
pytest
```

# Архитектура SkillFlow MVP

## Почему в первой версии код не был разбит по модулям диаграммы

В первой итерации я приоритизировал запуск MVP по вертикальным слоям (`api / models / repositories / services / static`), чтобы быстрее закрыть сквозной пользовательский сценарий: регистрация → создание теста → модерация → прохождение → рейтинг → Telegram.

Это **ускорило старт**, но **ухудшило читаемость относительно вашей диаграммы классов**, потому что модульные границы диаграммы (`Users`, `Content`, `Execution`, `Gamification`, `Integration`, `Data Access`) в файловой структуре не были показаны явно.

Ниже я зафиксировал это уже **в явном виде**, чтобы можно было буквально открыть файл и сказать:

- «вот модуль Users»;
- «вот модуль Content»;
- «вот здесь лежит State Machine»;
- «вот здесь лежит Strategy».

---

## Соответствие модулей диаграммы и кода

### 1. USERS MODULE

**Файлы:**
- `app/modules/users/__init__.py`
- `app/models/entities.py` → `User`
- `app/services/auth_service.py`
- `app/dependencies.py`

**Что внутри:**
- сущность пользователя;
- логика регистрации и входа;
- извлечение текущего пользователя по токену.

### 2. CONTENT MODULE

**Файлы:**
- `app/modules/content/__init__.py`
- `app/models/entities.py` → `Subject`, `Test`, `Question`, `AnswerOption`
- `app/services/state_machine.py`
- `app/services/question_factory.py`

**Что внутри:**
- тесты, предметы, вопросы, варианты ответов;
- жизненный цикл теста;
- фабрика создания вопросов.

### 3. EXECUTION MODULE

**Файлы:**
- `app/modules/execution/__init__.py`
- `app/models/entities.py` → `TestAttempt`, `UserAnswer`
- `app/services/test_service.py`

**Что внутри:**
- попытки прохождения теста;
- проверка ответов;
- вычисление результата теста.

### 4. GAMIFICATION MODULE

**Файлы:**
- `app/modules/gamification/__init__.py`
- `app/models/entities.py` → `Rating`, `Achievement`, `UserAchievement`
- `app/services/event_bus.py`
- `app/services/rating_strategy.py`
- `app/services/achievement_service.py`

**Что внутри:**
- рейтинг;
- достижения;
- события и подписчики;
- стратегии расчёта рейтинговых баллов.

### 5. INTEGRATION MODULE

**Файлы:**
- `app/modules/integration/__init__.py`
- `app/services/telegram_adapter.py`
- `bot/main.py`

**Что внутри:**
- Telegram Adapter;
- Telegram bot handlers.

### 6. DATA ACCESS MODULE

**Файлы:**
- `app/modules/data_access/__init__.py`
- `app/repositories/base.py`
- `app/repositories/user_repository.py`
- `app/repositories/test_repository.py`
- `app/repositories/attempt_repository.py`
- `app/repositories/rating_repository.py`
- `app/repositories/achievement_repository.py`

**Что внутри:**
- единый репозиторный слой доступа к данным.

---

## Где конкретно находятся паттерны

### Repository

**Паттерн расположен в:**
- `app/repositories/base.py` → базовый `Repository`
- `app/repositories/user_repository.py` → `UserRepository`
- `app/repositories/test_repository.py` → `TestRepository`
- `app/repositories/attempt_repository.py` → `AttemptRepository`
- `app/repositories/rating_repository.py` → `RatingRepository`
- `app/repositories/achievement_repository.py` → `AchievementRepository`

**Фраза, которую теперь можно использовать:**
> «Вот Data Access module, а вот внутри него — паттерн Repository».

### State Machine

**Паттерн расположен в:**
- `app/services/state_machine.py` → `TestStateMachine`

**Фраза:**
> «Вот Content module, а вот в файле `state_machine.py` лежит паттерн State Machine для жизненного цикла теста».

### Observer

**Паттерн расположен в:**
- `app/services/event_bus.py` → `EventBus`
- `app/services/test_service.py` → подписка на `TEST_COMPLETED` и `TEST_PUBLISHED`

**Фраза:**
> «Вот Gamification module: `EventBus` — это Observer, а `TestService` публикует события и подписывает обработчики».

### Strategy

**Паттерн расположен в:**
- `app/services/rating_strategy.py` → `RatingStrategy`, `StandardStrategy`, `BonusStrategy`, `TournamentStrategy`, `RatingStrategyFactory`
- `app/services/test_service.py` → выбор стратегии через `RatingStrategyFactory.build(...)`

**Фраза:**
> «Вот Gamification module, а вот в `rating_strategy.py` лежит паттерн Strategy для расчёта рейтинга».

### Factory Method

**Паттерн расположен в:**
- `app/services/question_factory.py` → `QuestionFactory`, `SingleChoiceQuestion`, `MultipleChoiceQuestion`
- `app/services/test_service.py` → вызов `QuestionFactory.create(...)`

**Фраза:**
> «Вот Content module, а вот в `question_factory.py` лежит Factory Method для создания разных типов вопросов».

### Adapter

**Паттерн расположен в:**
- `app/services/telegram_adapter.py` → `TelegramAdapter`
- `bot/main.py` → использование адаптера ботом

**Фраза:**
> «Вот Integration module, а вот в `telegram_adapter.py` расположен Adapter между Telegram-ботом и backend API».

---

## Как показывать это на защите / в отчёте

Короткий вариант:

1. **Сначала показываете модуль** из `app/modules/...`.
2. **Потом показываете сущности/сервисы**, которые относятся к нему.
3. **Потом показываете паттерн** конкретным файлом и классом.

Пример:

- `app/modules/content/__init__.py` → это **Content module**;
- `app/models/entities.py` (`Test`, `Question`, `AnswerOption`) → это сущности контентного модуля;
- `app/services/state_machine.py` (`TestStateMachine`) → это **State Machine**;
- `app/services/question_factory.py` (`QuestionFactory`) → это **Factory Method**.

Именно такого явного слоя в первой версии действительно не хватало.

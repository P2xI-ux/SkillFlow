# Merge Playbook (main compatibility)

Этот чеклист нужен, чтобы merge в `main` прошёл максимально гладко.

## 1) Подтянуть main и проверить конфликты
```bash
git fetch origin
git rebase origin/main
```

## 2) Если возникли конфликты — приоритеты
1. Сохранять бизнес-правила из `app/services/test_service.py`:
   - тесты проходит только STUDENT;
   - создание тестов только STUDENT;
   - строгая валидация payload попытки.
2. Сохранять валидацию `UserRegister` из `app/schemas.py`:
   - пароль (>=8, буква+цифра),
   - role-based обязательные поля.
3. Сохранять Telegram-ограничения в `app/api/routes.py` и `app/services/telegram_adapter.py`.
4. Сохранять readiness/logging изменения в `app/main.py`.

## 3) Проверить миграции Alembic
- Убедиться, что цепочка ревизий линейная:
  - `20260429_01` -> `20260517_02`
- Запуск:
```bash
alembic upgrade head
```

## 4) Минимальные smoke-checkи
```bash
python -m py_compile app/main.py app/services/test_service.py app/schemas.py bot/main.py
```

## 5) CI
- Проверить, что workflow `.github/workflows/ci.yml` запускается на PR.
- Убедиться, что в main не удалены шаги install/compile/test.

## 6) После merge
- Проверить endpoints:
  - `/health`
  - `/health/ready`
  - `/api/auth/register`
  - `/api/telegram/link-code`
  - `/api/tests/{id}/attempt`

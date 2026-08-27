# Habit Tracker — бэкенд трекера полезных привычек

Бэкенд-часть SPA-приложения для трекера полезных привычек по мотивам книги
Джеймса Клира «Атомные привычки». Пользователь описывает привычки в формате
«я буду [ДЕЙСТВИЕ] в [ВРЕМЯ] в [МЕСТО]», а сервис в нужное время присылает
ему напоминание в Telegram.

Стек: Django 5, Django REST Framework, Simple JWT, Celery + Celery Beat,
Redis, PostgreSQL, Telegram Bot API, drf-spectacular (Swagger/Redoc).

## Возможности

- Регистрация и авторизация по email/паролю (JWT).
- CRUD над собственными привычками с пагинацией (5 привычек на страницу).
- Список публичных привычек других пользователей (только чтение).
- Валидация привычек согласно ТЗ (см. раздел «Бизнес-правила»).
- Напоминания о привычках в Telegram по расписанию через Celery Beat.
- Подключение Telegram-аккаунта пользователя через webhook бота.
- Автоматическая документация API (Swagger / Redoc).

## Требования

- Python 3.11+
- PostgreSQL
- Redis (брокер и backend для Celery)

## Установка и запуск

1. Клонируйте репозиторий и перейдите в него:

   ```bash
   git clone <url-репозитория>
   cd habits_tracker
   ```

2. Создайте и активируйте виртуальное окружение:

   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate         # Windows
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` в корне проекта на основе `.env.template` и
   заполните своими значениями:

   ```env
   SECRET_KEY=django-insecure-change-me
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432

   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0

   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

   TELEGRAM_BOT_TOKEN=123456:ваш-токен-бота
   TELEGRAM_API_URL=https://api.telegram.org/bot
   ```

   > База данных по умолчанию называется `habits_tracker` (задано в
   > `config/settings.py`). Создайте её в PostgreSQL заранее:
   > `createdb habits_tracker`.

5. Примените миграции и создайте суперпользователя:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. Запустите сервер разработки:

   ```bash
   python manage.py runserver
   ```

   API будет доступно на `http://127.0.0.1:8000/`.

### Запуск Celery (напоминания в Telegram)

Для рассылки напоминаний по расписанию нужны воркер и планировщик Celery
(в отдельных терминалах, Redis должен быть запущен):

```bash
celery -A config worker -l info
celery -A config beat -l info
```

Расписание задаётся в `CELERY_BEAT_SCHEDULE` (`config/settings.py`):
задача `habits.tasks.send_habit_reminders` запускается каждую минуту и
рассылает напоминания тем пользователям, у кого наступило время
выполнения привычки и подключён Telegram.

### Подключение Telegram-бота

1. Создайте бота через [@BotFather](https://t.me/BotFather), получите
   токен и укажите его в `TELEGRAM_BOT_TOKEN`.
2. Настройте webhook бота на эндпоинт `POST /habits/telegram/webhook/`
   (сервер должен быть доступен по HTTPS), например:

   ```bash
   curl -F "url=https://ваш-домен/habits/telegram/webhook/" \
        https://api.telegram.org/bot<ТОКЕН>/setWebhook
   ```

3. Пользователь пишет боту `/start`. Webhook сопоставляет Telegram
   `username` из апдейта с `username` зарегистрированного пользователя
   и сохраняет `telegram_chat_id` — после этого ему начинают приходить
   напоминания.

## Документация API

После запуска сервера документация доступна по адресам:

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- Redoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI-схема: `http://127.0.0.1:8000/api/schema/`

## Основные эндпоинты

| Метод | Путь | Описание | Доступ |
|---|---|---|---|
| POST | `/users/register/` | Регистрация нового пользователя | Открыт |
| POST | `/users/login/` | Получение пары JWT-токенов (access/refresh) | Открыт |
| POST | `/users/login/refresh/` | Обновление access-токена | Открыт |
| GET/PATCH | `/users/profile/` | Просмотр/редактирование своего профиля | Авторизован |
| GET | `/habits/` | Список своих привычек (пагинация, 5 на страницу) | Авторизован |
| POST | `/habits/` | Создание привычки | Авторизован |
| GET | `/habits/<id>/` | Детали своей привычки | Владелец |
| PUT/PATCH | `/habits/<id>/` | Редактирование своей привычки | Владелец |
| DELETE | `/habits/<id>/` | Удаление своей привычки | Владелец |
| GET | `/habits/public/` | Список публичных привычек (только чтение) | Авторизован |
| POST | `/habits/telegram/webhook/` | Webhook для Telegram-бота | Открыт (для Telegram) |
| \* | `/admin/` | Django-админка | Staff |

## Модель привычки

Поля модели `Habit` (`habits/models.py`): `user`, `place`, `time`, `action`,
`is_pleasant`, `related_habit`, `periodicity` (дней, по умолчанию 1),
`reward`, `duration` (сек.), `is_public`, `created_at`.

### Бизнес-правила и валидация (`habits/validators.py`)

- Нельзя одновременно указывать `reward` и `related_habit`.
- `duration` не может превышать 120 секунд.
- В `related_habit` можно выбрать только привычку с `is_pleasant=True`.
- У приятной привычки (`is_pleasant=True`) не может быть ни `reward`,
  ни `related_habit`.
- `periodicity` — от 1 до 7 дней (нельзя выполнять привычку реже,
  чем раз в неделю).
- В `related_habit` нельзя указать чужую привычку (`serializers.py`).

### Права доступа

- CRUD над привычкой доступен только её владельцу (`IsOwner`).
- Список `/habits/public/` виден всем авторизованным пользователям,
  но доступен только на чтение — редактировать или удалять чужие
  публичные привычки нельзя.

## Тесты и покрытие

Тесты лежат в `habits/tests/` (`test_habits.py`, `test_validators.py`,
`test_tasks.py`, `test_webhook.py`) и `users/tests/` (`test_users.py`).

Запуск тестов:

```bash
python manage.py test
```

Запуск с проверкой покрытия (порог — 80%+):

```bash
coverage run --source='.' manage.py test
coverage report
coverage html   # подробный отчёт в htmlcov/index.html
```

## Проверка стиля кода (PEP 8)

Конфигурация flake8 — в `setup.cfg` (длина строки до 119 символов,
миграции и виртуальное окружение исключены):

```bash
flake8
```

## Переменные окружения

Все настройки, зависящие от окружения, вынесены в `.env` (сам файл в
`.gitignore` и не коммитится). Пример со всеми переменными — в
`.env.template`:

| Переменная | Назначение |
|---|---|
| `SECRET_KEY` | Секретный ключ Django |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Подключение к PostgreSQL |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` | Подключение к Redis (брокер Celery) |
| `CORS_ALLOWED_ORIGINS` | Список разрешённых доменов фронтенда (через запятую) |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота, полученный от BotFather |
| `TELEGRAM_API_URL` | Базовый URL Telegram Bot API |

## Структура проекта

```
config/          настройки Django, Celery, корневые urls
users/           кастомная модель пользователя, регистрация, JWT-авторизация
habits/          модель привычки, эндпоинты, валидаторы, celery-задачи, Telegram
```
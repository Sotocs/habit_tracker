# Habit Tracker API

REST API для создания и отслеживания привычек. Проект разработан на Django REST Framework и поддерживает JWT-аутентификацию, публичные привычки, пагинацию и Telegram-напоминания с использованием Celery и Redis.

## Стек технологий

* Python 3.14+
* Django
* Django REST Framework
* PostgreSQL
* Simple JWT
* Celery
* Redis
* drf-spectacular (Swagger / OpenAPI)
* Telegram Bot API

## 1. Требования

Перед запуском установите:

* Python;
* Poetry;
* PostgreSQL;
* Redis.

Для отправки Telegram-уведомлений необходим доступ к Telegram Bot API.

## 2. Клонирование проекта

```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ>
cd habit_tracker
```

Установите зависимости:

```bash
poetry install
```

Активируйте виртуальное окружение:

```bash
poetry shell
```

Если команда `poetry shell` недоступна в вашей версии Poetry, используйте `poetry run` перед командами проекта.

## 3. Настройка переменных окружения

В корне проекта создайте файл `.env` на основе `.env.template`.

В PowerShell:

```powershell
Copy-Item .env.template .env
```

Пример содержимого `.env`:

```dotenv
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=habit_tracker
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

TELEGRAM_BOT_TOKEN=
```

Названия переменных должны соответствовать настройкам в `config/settings.py`. Если в проекте используются дополнительные переменные, добавьте их в `.env` и `.env.template`.

**Важно:** не публикуйте `.env`, пароли, секретный ключ Django или токен Telegram-бота в GitHub. Для production-среды установите `DEBUG=False` и используйте собственный секретный ключ.

## 4. Настройка PostgreSQL

Создайте базу данных PostgreSQL с именем, указанным в `DB_NAME`.

Например, через `psql`:

```sql
CREATE DATABASE habit_tracker;
```

Убедитесь, что пользователь PostgreSQL, указанный в `DB_USER`, имеет права на подключение к базе и выполнение необходимых операций.

Примените миграции:

```bash
poetry run python manage.py migrate
```

Создайте администратора:

```bash
poetry run python manage.py createsuperuser
```

Проверьте конфигурацию Django:

```bash
poetry run python manage.py check
```

## 5. Запуск Redis

Убедитесь, что Redis запущен и доступен по адресу, указанному в `REDIS_URL`.

Для локального Redis по умолчанию используется:

```text
redis://localhost:6379/0
```

Если Redis установлен локально, запустите его способом, соответствующим вашей операционной системе.

Проверить доступность можно командой:

```bash
redis-cli ping
```

Ожидаемый ответ:

```text
PONG
```

## 6. Настройка Telegram-бота

### 6.1. Создание бота

1. Откройте Telegram и найдите официального бота [@BotFather](https://t.me/BotFather).
2. Отправьте команду `/newbot`.
3. Укажите имя и username нового бота.
4. Скопируйте полученный токен.
5. Добавьте токен в `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

Не публикуйте токен в исходном коде, сообщениях или публичном репозитории. Если токен стал доступен посторонним, отзовите его через BotFather и создайте новый.

### 6.2. Получение Telegram Chat ID

1. Откройте созданного бота по ссылке, выданной BotFather.
2. Нажмите **Start** или отправьте `/start`.
3. Получите обновления бота через Telegram Bot API методом `getUpdates`, используя актуальный токен.
4. Найдите поле `message.chat.id` в ответе.

Не публикуйте URL с токеном или полный ответ API, если он содержит конфиденциальные данные.

Если `getUpdates` возвращает пустой список, отправьте боту новое сообщение и повторите запрос. Если настроен webhook, сначала проверьте его состояние: при активном webhook метод `getUpdates` может быть недоступен.

### 6.3. Привязка Chat ID к пользователю

В проекте предусмотрено поле `telegram_chat_id` у модели пользователя.

Откройте административную панель:

```text
http://127.0.0.1:8000/admin/
```

Войдите под администратором, откройте нужного пользователя и укажите его Telegram Chat ID в соответствующем поле. Сохраните изменения.

Также убедитесь, что пользователь действительно начал диалог с ботом: Telegram не позволяет боту первым написать пользователю в обычном личном чате.

## 7. Запуск приложения

Запустите Django:

```bash
poetry run python manage.py runserver
```

API будет доступен по адресу:

```text
http://127.0.0.1:8000/
```

Административная панель:

```text
http://127.0.0.1:8000/admin/
```

## 8. Запуск Celery Worker и Celery Beat

Для работы напоминаний необходимы два отдельных процесса Celery и работающий Redis.

### Терминал 1 — Worker

```bash
poetry run celery -A config worker --loglevel=info --pool=solo
```

Параметр `--pool=solo` подходит для локального запуска в Windows.

### Терминал 2 — Beat

```bash
poetry run celery -A config beat --loglevel=info
```

Celery Beat запускает задачу отправки напоминаний по расписанию, настроенному в `config/settings.py`. В текущей конфигурации задача запускается каждую минуту.

Для локальной разработки все три процесса — Django, Worker и Beat — должны работать одновременно.

## 9. Как работают напоминания

Задача `send_habit_reminders` выполняет следующие действия:

1. Находит привычки, время которых совпадает с текущими часом и минутой.
2. Проверяет наличие Telegram Chat ID у владельца.
3. Учитывает периодичность привычки.
4. Формирует сообщение с действием, местом и временем выполнения.
5. Отправляет сообщение через Telegram Bot API.

Для отправки уведомления необходимо, чтобы:

* в `.env` был указан действующий токен;
* у пользователя был заполнен `telegram_chat_id`;
* время привычки совпадало со временем выполнения задачи;
* наступил подходящий день по заданной периодичности;
* Worker и Beat работали, а Redis был доступен;
* сервер мог подключиться к Telegram Bot API.

Если задача завершилась с результатом `0`, это означает, что она не зарегистрировала успешных отправок в данном запуске. Проверьте время привычки, периодичность, Chat ID и журналы Worker.

## 10. Документация API

После запуска Django доступны следующие страницы:

| Адрес          | Описание                                |
| -------------- | --------------------------------------- |
| `/api/docs/`   | Swagger UI — интерактивная документация |
| `/api/redoc/`  | ReDoc — справочник API                  |
| `/api/schema/` | OpenAPI-схема                           |

Основные эндпоинты:

| Метод  | Эндпоинт               | Назначение                    |
| ------ | ---------------------- | ----------------------------- |
| POST   | `/api/users/register/` | Регистрация пользователя      |
| POST   | `/api/token/`          | Получение JWT-токенов         |
| POST   | `/api/token/refresh/`  | Обновление access-токена      |
| GET    | `/api/habits/`         | Список своих привычек         |
| POST   | `/api/habits/`         | Создание привычки             |
| GET    | `/api/habits/public/`  | Список публичных привычек     |
| GET    | `/api/habits/{id}/`    | Просмотр привычки             |
| PUT    | `/api/habits/{id}/`    | Полное обновление привычки    |
| PATCH  | `/api/habits/{id}/`    | Частичное обновление привычки |
| DELETE | `/api/habits/{id}/`    | Удаление привычки             |

Для защищённых эндпоинтов используйте JWT access-токен. В Swagger нажмите **Authorize** и укажите токен в формате `Bearer <access-токен>`, если интерфейс не добавляет префикс автоматически.

Для списков привычек предусмотрена пагинация с параметрами `limit` и `offset`.

## 11. Проверка проекта

Проверка конфигурации:

```bash
poetry run python manage.py check
```

Проверка миграций:

```bash
poetry run python manage.py makemigrations --check --dry-run
```

Запуск тестов:

```bash
poetry run python manage.py test
```

Проверка покрытия тестами:

```bash
poetry run coverage run manage.py test
poetry run coverage report -m
```

Проверка генерации OpenAPI-схемы:

```bash
poetry run python manage.py spectacular --validate --file schema.yml
```

## 12. Структура проекта

```text
habit_tracker/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── __init__.py
├── habits/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── permissions.py
│   ├── tasks.py
│   ├── urls.py
│   └── tests.py
├── users/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── .env.template
├── .gitignore
├── manage.py
├── pyproject.toml
└── poetry.lock
```

## 13. Примечания

* `.env` содержит локальные секреты и не должен попадать в репозиторий.
* `.env.template` используется как образец конфигурации без реальных секретов.
* PostgreSQL и Redis должны быть запущены до старта соответствующих процессов приложения.
* Telegram-уведомления зависят от доступности Telegram Bot API и правильности настройки бота.
* Перед развёртыванием в production необходимо настроить безопасные параметры Django, доступ к базе данных, секреты и инфраструктуру.

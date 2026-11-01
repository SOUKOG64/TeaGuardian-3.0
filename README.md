# TeaGuardian: чайный дневник

Мобильное приложение (Kivy) + сервер (FastAPI, SQLAlchemy, SQLite).
Приложение работает только через API сервера. Раздел «Чайные знания» работает без сервера.

## Структура

```
main.py, api.py, widgets.py, tea.kv, articles.py   клиент (Kivy)
screens/                                            по файлу на экран
server/app/                                         сервер
    api/           маршруты (HTTP)
    services/      бизнес-логика
    repositories/  работа с БД (SQLAlchemy select/commit/rollback)
    models.py      таблицы, schemas.py: схемы Pydantic
server/tests/                                       тесты API
```

## Запуск сервера (на компьютере)

```
cd server
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Документация API (Swagger): http://localhost:8000/docs

Тесты: `pip install pytest httpx`, затем `python -m pytest tests -q` (из папки server).

Необязательно: `TEA_ADMIN=логин` задаёт логин, который при регистрации станет администратором
(администратор видит записи всех пользователей). По умолчанию администратора нет.

## Доступ с телефона через туннель

Пока сервер запущен, в соседнем окне терминала:

```
cloudflared tunnel --url http://localhost:8000
```

Он выведет адрес вида `https://что-то.trycloudflare.com`. Его нужно вписать в поле
«Адрес сервера» на экране входа. При каждом новом запуске туннеля адрес другой: просто впишите новый,
пересобирать APK не нужно.

Вместо туннеля можно использовать Wi-Fi: телефон и компьютер в одной сети,
адрес `192.168.x.x:8000` (IP компьютера), порт 8000 должен быть разрешён в брандмауэре.

## Запуск клиента на компьютере (для проверки)

```
pip install kivy certifi
python main.py
```

## Сборка APK

Файлы лежат в репозитории GitHub, сборка запускается сама (вкладка Actions).
Папка `server` в APK не попадает.

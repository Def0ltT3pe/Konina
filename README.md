# Konina

Сервис мониторинга цен на товары с маркетплейсов: **Wildberries**, **AliExpress** и **Яндекс.Маркет**.

Backend принимает ссылку на товар, открывает страницу через Selenium (Firefox + geckodriver), вытаскивает название и цену, складывает результат в SQLite и отдаёт клиенту. Доступ к методам парсинга защищён JWT-аутентификацией (токен в cookie). Есть заготовка фонового обновления цен по расписанию.

> ⚠️ Проект учебный и находится в стадии разработки (последний коммит — апрель 2025). Часть модулей — черновики и дубликаты, известные проблемы перечислены в разделе [Известные проблемы](#известные-проблемы).

---

## Возможности

- 🔐 Регистрация и вход пользователей, JWT в cookie (`authx`), пароли хешируются `bcrypt`.
- 🛒 Парсинг карточки товара по ссылке или по идентификатору для трёх маркетплейсов.
- 💾 Хранение товаров (SKU, название, цена, маркетплейс) в SQLite через SQLAlchemy ORM.
- ♻️ Проверка дублей: повторный парсинг того же товара не создаёт новую запись.
- 🧵 Парсинг выполняется в пуле потоков (`ThreadPoolExecutor`), поэтому обработчики FastAPI остаются асинхронными.
- ⏰ Заготовка планировщика (`rocketry`) для ежедневного обновления цен.
- 🌐 CORS настроен на локальный фронтенд: `http://localhost`, `http://localhost:5173`, `http://localhost:5174`.

## Стек

| Слой | Технологии |
|---|---|
| API | FastAPI, Uvicorn, Pydantic |
| Аутентификация | authx (JWT в cookie), passlib + bcrypt |
| База данных | SQLAlchemy ORM, SQLite (`data_base.db`) |
| Парсинг | Selenium WebDriver (Firefox), webdriver-manager, geckodriver 0.36.0 |
| Планировщик | Rocketry |
| Язык | Python |

## Структура проекта

```
Konina/
├── main.py                 # Точка входа FastAPI: авторизация + эндпоинты парсинга
├── DB.py                   # Модели Product/User, подключение к SQLite, работа с паролями
├── auto_parser.py          # Роутер /parse/auto: определяет маркетплейс по домену ссылки
├── scheduler.py            # Планировщик обновления цен (Rocketry, задача после 15:30)
├── parser_wb.py            # Парсер Wildberries (актуальный)
├── parser_aliexpress.py    # Парсер AliExpress (актуальный)
├── parser_ym.py            # Парсер Яндекс.Маркета (актуальный)
├── parse_wb_price.py       # Черновик парсера WB
├── parser_wb1.py           # Черновик парсера WB (получение только цены)
├── parser_ym1.py           # Черновик парсера Яндекс.Маркета
├── celenium_test.py        # Тестовый запуск Selenium
├── celenium_OZON.py        # Черновик: Selenium + AliExpress (несмотря на имя файла)
├── main12.py               # Ранняя версия API (без БД и авторизации)
├── data_base.db            # SQLite-база (в репозитории уже есть)
├── requirements            # Список зависимостей (неполный, см. ниже)
└── geckodriver-v0.36.0-win64/geckodriver.exe
```

## Требования

- **Python 3.11+** (в репозитории есть байткод для 3.13)
- **Firefox** — Selenium запускает именно его
- **geckodriver** — либо положить в `PATH`, либо прописать путь в коде (см. [Настройку](#настройка))
- ОС: разработка велась под Windows

## Установка

```bash
git clone https://github.com/Def0ltT3pe/Konina.git
cd Konina

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
```

Зависимости:

```bash
pip install -r requirements

# Файл requirements неполный — отдельно доустановите:
pip install selenium webdriver-manager authx passlib bcrypt rocketry
```

> В `requirements` указаны только `fastapi`, `uvicorn`, `sqlalchemy` и `aiosqlite`, хотя код импортирует ещё `selenium`, `webdriver_manager`, `authx`, `passlib` и `rocketry`.

## Настройка

1. **Путь к geckodriver.** Сейчас он захардкожен под машину разработчика в `parser_aliexpress.py`:

   ```python
   service = Service("C:\\Users\\svobo\\Documents\\GitHub\\Konina\\geckodriver-v0.36.0-win64\\geckodriver.exe")
   ```

   Укажите свой путь. В `parser_wb.py` и `parser_ym.py` драйвер ставится автоматически через `webdriver-manager`, там правки не нужны.

2. **Секретный ключ JWT.** В `main.py` ключ зашит в код:

   ```python
   config.JWT_SECRET_KEY = "SECRET_KEY"
   ```

   Для реального использования вынесите его в переменную окружения.

3. **Браузер.** Парсеры по умолчанию работают **не в headless-режиме** (окно Firefox будет открываться). Чтобы отключить показ окна, раскомментируйте `options.add_argument('--headless')` в нужном парсере.

База данных создаётся автоматически при первом импорте `DB.py` (`Base.metadata.create_all(bind=engine)`) в файле `data_base.db` рядом с проектом.

## Запуск

```bash
uvicorn main:app --host localhost --port 8000
# или
python main.py
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

Планировщик запускается отдельно:

```bash
python scheduler.py
```

## API

Базовый URL: `http://localhost:8000`

### Аутентификация

Все эндпоинты парсинга требуют cookie с JWT. Cookie `my_access_token` ставится автоматически ответами `/login` и `/register`, поэтому в браузере достаточно `credentials: "include"`, а в curl — сохранить cookie-файл.

#### `POST /register`

Создаёт пользователя. Если e-mail уже занят — `409`.

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

Ответ:

```json
{ "access_token": true }
```

#### `POST /login`

Проверяет пару e-mail/пароль. При неверных данных — `401`.

Тело запроса — такое же, как у `/register`.

#### `GET /protected`

Тестовый защищённый эндпоинт.

```json
{ "data": "СЕКРЕТНАЯ КОНИНА" }
```

### Парсинг

#### `GET /parse/wb?url=<ссылка>`

Ссылка на товар Wildberries. `nm_id` извлекается из пути и должен находиться на предпоследней позиции.

```bash
curl -b cookies.txt -c cookies.txt \
  "http://localhost:8000/parse/wb?url=https://www.wildberries.ru/catalog/102855978760/detail.aspx"
```

Ответ:

```json
{
  "nm_id": 102855978760,
  "name": "Наушники беспроводные",
  "price": 2499.0,
  "marketplace": "Wildberries",
  "image": "https://.../photo.jpg"
}
```

Если товар уже есть в базе, вернётся `{"message": "Продукт с таким nm_id уже существует.", "data": {...}}`.

#### `GET /parse/aliexpress?url=<ссылка>`

Ссылка на товар AliExpress. `sku_id` берётся из query-параметра `sku_id`, а если его нет — ищется регулярным выражением в исходном коде страницы.

Ответ:

```json
{
  "sku_id": "12000044268637948",
  "name": "Название товара",
  "price": "1234",
  "marketplace": "Aliexpress"
}
```

> Обратите внимание: цена и `sku_id` здесь возвращаются строками, а в `/parse/wb` цена — число.

#### `GET /parse/ym?url=<ссылка>`

Ссылка на товар Яндекс.Маркета. Из query извлекается `sku`, из пути — `product_id`. Если оба параметра не найдены — `400`.

```bash
curl -b cookies.txt -c cookies.txt \
  "http://localhost:8000/parse/ym?url=https://market.yandex.ru/product--watch-pro-2/861347316?sku=103757197929"
```

Ответ:

```json
{
  "nm_id": 103757197929,
  "name": "Смарт-часы Watch Pro 2",
  "price": 5990,
  "marketplace": "Яндекс маркет"
}
```

#### `GET /parse/auto?url=<ссылка>`

Автоматическое определение маркетплейса по домену ссылки (`wildberries.ru`, `aliexpress`, `market.yandex`) и вызов нужного парсера. Неизвестный домен — `400`:

```json
{ "detail": "Неизвестный источник ссылки." }
```

> ⚠️ Роутер из `auto_parser.py` не подключён к приложению в `main.py`, поэтому по умолчанию этот эндпоинт недоступен. Чтобы включить его, добавьте в `main.py`:
>
> ```python
> from auto_parser import router as auto_router
> app.include_router(auto_router)
> ```

## Схема базы данных

`products`

| Поле | Тип | Описание |
|---|---|---|
| `sku_id` | Integer, PK | Идентификатор товара на маркетплейсе |
| `name` | String | Название товара |
| `price` | Float | Цена |
| `marketplace` | String | Источник (`Wildberries`, `Aliexpress`, `Яндекс маркет`) |

`users`

| Поле | Тип | Описание |
|---|---|---|
| `user_email` | String, PK | E-mail пользователя |
| `password` | String | Хеш пароля (bcrypt) |

## Планировщик

`scheduler.py` создаёт приложение Rocketry с задачей `update_all_aliexpress`, которая запускается ежедневно после 15:30 и обновляет записи товаров AliExpress.

> На текущий момент функция нерабочая: в `ProductModel.sku_id` выбирается колонка идентификаторов, после чего код обращается к `product.sku_id` как к объекту. Кроме того, обновление передаёт в парсер `sku_id` вместо ссылки на товар, которую ожидает `get_aliexpress_data(url)`. Модуль стоит рассматривать как каркас для доработки.

## Известные проблемы

- **Жёсткие пути под Windows.** `parser_aliexpress.py`, `parser_wb1.py`, `celenium_test.py` и `celenium_OZON.py` содержат абсолютные пути вида `C:\Users\svobo\...` и `D:\Konina\...`, которые придётся менять вручную.
- **Секреты в коде.** `JWT_SECRET_KEY = "SECRET_KEY"` задан прямо в `main.py`.
- **Неполный `requirements`.** Часть зависимостей не задекларирована.
- **Отсутствует `.gitignore`.** В репозиторий попали `__pycache__/`, `.idea/`, `.vs/`, `data_base.db` и бинарник `geckodriver.exe` (~4.4 МБ).
- **Дубликаты и черновики.** `main12.py`, `parse_wb_price.py`, `parser_wb1.py`, `parser_ym1.py`, `celenium_test.py`, `celenium_OZON.py` — мёртвый код или ранние версии; `parser_ym1.py` почти полностью повторяет `parser_ym.py`.
- **Нет асинхронного доступа к БД.** В `requirements` есть `aiosqlite`, но фактически используется синхронный SQLAlchemy внутри FastAPI-обработчиков.
- **Хрупкие селекторы.** Парсеры завязаны на CSS-классы маркетплейсов (например, `HazeProductPrice_SnowPrice__mainS__1wzo3`) и сломаются при обновлении вёрстки.
- **Ошибки парсинга маскируются под данные.** При неудаче в поле `name` или `price` попадает строка `"Ошибка: ..."`.
- **Нет тестов** и нет Docker-конфигурации.

## Идеи для развития

- Вынести пути к драйверу и секреты в переменные окружения (`.env`).
- Актуализировать `requirements` или перейти на `pyproject.toml`.
- Добавить `.gitignore` и убрать из репозитория базу, кеш и бинарники.
- Починить `scheduler.py` и подключить `auto_parser.py` к приложению.
- Добавить эндпоинты для чтения списка отслеживаемых товаров и истории цен.
- Заменить Selenium на HTTP-клиент или официальные API маркетплейсов там, где это возможно, — это сильно ускорит и упростит парсинг.
- Написать тесты (pytest) с моками парсеров.

## Авторы

- [Def0ltT3pe](https://github.com/Def0ltT3pe)
- [vvinokura](https://github.com/vvinokura)

## Лицензия

Лицензия в репозитории не указана. Если планируете использовать проект, добавьте файл `LICENSE`.

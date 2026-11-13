<p align="center">
  <img src="docs/assets/TerraData.svg" alt="TerraData" width="480" />
</p>

TerraData — это API-сервис для работы с государственными геоданными и сведениями об объектах недвижимости. Он объединяет взаимодействие с несколькими источниками:

- **Росреестр** — получение сведений об объектах недвижимости по кадастровым номерам и поиск по адресу, конвертация XML-выписок в PDF с автоматическим решением капчи.
- **НСПД** (Национальная система пространственных данных) — кадастровая стоимость и полные сведения об объектах недвижимости.
- **ФИАС** — адресный реестр: поиск адресов и объектов по кадастровым номерам и ObjectID.
- **СУДРФ** (ГАС «Правосудие») — определение судебного участка по адресу или кадастровому номеру.

## 🚀 Возможности

- **Росреестр**: получение полных сырых данных об объекте по кадастровому номеру, поиск кадастровых номеров по адресу.
- **Конвертация XML в PDF**: загрузка XML-выписки и получение отформатированного PDF-документа.
- **Автоматическое решение капчи**: OCR-модель на базе TensorFlow/Keras для распознавания капчи Росреестра.
- **НСПД**: кадастровая стоимость и детальные сведения по объектам (здания, земельные участки, помещения) с конвертацией геометрии.
- **ФИАС**: поиск адресов, получение ObjectID и сведений по кадастровому номеру.
- **СУДРФ**: определение судебного участка по кадастровому номеру, адресу или ObjectID ФИАС.
- **Аналитические PDF-отчёты**: агрегация данных из Росреестра, НСПД, ФИАС и СУДРФ в единый PDF-документ по кадастровому номеру.
- **Аутентификация и авторизация**: регистрация/вход (JWT), API-ключи, роли `admin`/`user`, суточные квоты запросов.
- **Современный API**: построен на FastAPI с автоматической генерацией OpenAPI-документации.

## 🛠 Технологический стек

- **Язык**: Python 3.10+
- **Фреймворк**: [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **OCR/ML**: [TensorFlow](https://www.tensorflow.org/) и [Keras](https://keras.io/), OpenCV, Pillow
- **HTTP-клиент**: [HTTPX](https://www.encode.io/httpx/), [Requests](https://requests.readthedocs.io/)
- **Генерация PDF**: [pdfkit](https://pypi.org/project/pdfkit/) (конвертация XML-выписок, требуется `wkhtmltopdf`), [ReportLab](https://pypi.org/project/reportlab/) (аналитические отчёты)
- **Данные**: [pandas](https://pandas.pydata.org/)
- **Тестирование**: [pytest](https://docs.pytest.org/), pytest-asyncio
- **Документация**: [MkDocs](https://www.mkdocs.org/) + Material
- **Развертывание**: Docker и Docker Compose

## 📋 Предварительные требования

Перед запуском приложения убедитесь, что установлено следующее:
- Python 3.10 или выше
- [wkhtmltopdf](https://wkhtmltopdf.org/downloads.html) (необходимо для конвертации в PDF; при запуске в Docker устанавливается автоматически)

## ⚙️ Установка и настройка

### Локальный запуск

1. **Клонирование репозитория**:
   ```bash
   git clone <repository-url>
   cd TerraData
   ```

2. **Создание и активация виртуального окружения**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Windows: venv\Scripts\activate
   ```

3. **Установка зависимостей**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Запуск приложения**:
   ```bash
   python main.py
   ```
   API будет доступно по адресу `http://localhost:8000`.

### Запуск в Docker

```bash
docker compose up --build
```

Сервис поднимется на `http://localhost:8000`, локальная папка `data/` монтируется в контейнер для сохранения отчетов и чтения XML.

## 🔌 API Эндпоинты

После запуска сервера доступна интерактивная документация Swagger по адресу `/docs` (и ReDoc по `/redoc`).

### Данные Росреестра
| Эндпоинт | Метод | Описание |
| :--- | :--- | :--- |
| `/rosreestr/info` | `GET` | Получение полной информации по кадастровому номеру |
| `/rosreestr/search-address` | `GET` | Поиск кадастровых номеров по адресу |

### Конвертер PDF
| Эндпоинт | Метод | Описание |
| :--- | :--- | :--- |
| `/converter/xml-to-pdf` | `POST` | Конвертация загруженного XML-файла в PDF |

### Данные НСПД
| Эндпоинт | Метод | Описание |
| :--- | :--- | :--- |
| `/nspd/cadastral-price` | `GET` | Кадастровая стоимость и базовые сведения об объекте |
| `/nspd/property` | `GET` | Полные сведения об объекте (здание, ЗУ или помещение) |
| `/nspd/details/objects-list` | `GET` | Список объектов здания |
| `/nspd/details/land-links` | `GET` | Связи объекта с земельными участками |
| `/nspd/details/build-parts` | `GET` | Части здания |
| `/nspd/details/permission-types` | `GET` | Виды разрешённого использования |

### Данные ФИАС
| Эндпоинт | Метод | Описание |
| :--- | :--- | :--- |
| `/fias/by-cadastral` | `GET` | Сведения ФИАС по кадастровому номеру |
| `/fias/search-address` | `GET` | Подсказки вариантов адреса в ФИАС |
| `/fias/by-object-id` | `GET` | Детальные сведения по ObjectID ФИАС |
| `/fias/object-id-by-cadastral` | `GET` | Получение ObjectID ФИАС по кадастровому номеру |

### Данные СУДРФ (судебные участки)
| Эндпоинт | Метод | Описание |
| :--- | :--- | :--- |
| `/sudrf/by-cadastral` | `GET` | Судебный участок по кадастровому номеру |
| `/sudrf/by-address` | `GET` | Судебный участок по адресу |
| `/sudrf/by-object-id` | `GET` | Судебный участок по ObjectID ФИАС |

### Аналитические PDF-отчёты
| Эндпоинт | Метод | Описание |
| :--- | :--- | :--- |
| `/analytics/generate-report` | `POST` | Генерация PDF-отчёта по кадастровому номеру (Росреестр + НСПД + ФИАС + СУДРФ) |

Тело запроса `POST /analytics/generate-report`:

```json
{
  "cad_num": "38:00:000000:00001",
  "include_nspd": true,
  "include_fias": true,
  "include_sudrf": true
}
```

Росреестр — ядро отчёта (собирается всегда), остальные источники включаются флагами; при недоступности источника соответствующая секция помечается как «данные недоступны».

### Аутентификация и авторизация

Все эндпоинты, кроме `POST /converter/xml-to-pdf`, `/auth/register`, `/auth/login` и служебных, требуют JWT (`Authorization: Bearer`) или активный API-ключ (`X-API-Key`).

| Эндпоинт | Метод | Описание |
| :--- | :--- | :--- |
| `/auth/register` | `POST` | Регистрация пользователя |
| `/auth/login` | `POST` | Вход и получение JWT |
| `/auth/me` | `GET` | Текущий пользователь |
| `/auth/api-keys` | `POST` | Создать API-ключ (полный ключ показывается один раз) |
| `/auth/api-keys` | `GET` | Список своих ключей |
| `/auth/api-keys/{id}` | `PATCH` | Активировать/деактивировать ключ |
| `/auth/api-keys/{id}` | `DELETE` | Отозвать ключ |

Админ-эндпоинты (роль `admin`):

| Эндпоинт | Метод | Описание |
| :--- | :--- | :--- |
| `/admin/users` | `GET` | Список пользователей |
| `/admin/users/{id}` | `GET/PATCH/DELETE` | Управление пользователем |
| `/admin/api-keys` | `GET` | Все ключи |
| `/admin/api-keys/{id}` | `DELETE` | Отозвать любой ключ |

Настройки задаются в `.env` (см. `.env.example`): `DATABASE_URL`, `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `DEFAULT_DAILY_QUOTA` и др.

## 📂 Структура проекта

```text
TerraData/
├── app/
│   ├── api/                # Маршруты API (rosreestr, converter, nspd, fias, sudrf, analytics, auth, admin)
│   ├── core/               # Конфигурация, БД, безопасность, зависимости авторизации
│   ├── models/             # ORM-модели (User, ApiKey, UsageRecord) и ML-модель (pred.keras)
│   ├── schemas/            # Pydantic-схемы
│   └── services/           # Бизнес-логика (клиенты, auth_service, конвертеры, PDF)
│       └── types/          # Словари типов
├── alembic/                # Миграции схемы БД
├── docs/                   # Документация (MkDocs)
├── tests/                  # Тесты Pytest и моки
├── .env.example            # Пример переменных окружения
├── Dockerfile              # Контейнеризация
├── docker-compose.yml      # Конфигурация Docker Compose (app + PostgreSQL)
├── main.py                 # Точка входа FastAPI
├── requirements.txt        # Зависимости
├── mkdocs.yml              # Конфигурация документации
├── pytest.ini              # Конфигурация pytest
├── README.md               # Описание проекта
├── PROJECT_STATE.md        # Текущее состояние проекта
└── ROADMAP.md              # Дорожная карта проекта
```

## 🧪 Тестирование

Запуск тестов с помощью pytest:
```bash
pytest .\tests\test_terradata.py
```

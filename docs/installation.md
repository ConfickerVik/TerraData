# Руководство по установке

На этой странице описано, как настроить TerraData на локальной машине или в контейнеризированной среде.

## Системные требования

### Программное обеспечение
- **Python 3.10+**: Проект использует современную типизацию Python и `asyncio`.
- **wkhtmltopdf**: Критическая системная зависимость для сервиса конвертации в PDF.
  - **Windows**: Скачайте с [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html).
  - **Linux**: `sudo apt-get install wkhtmltopdf`

## Локальная установка

1. **Клонирование репозитория**
   ```bash
   git clone <your-repo-url>
   cd TerraData
   ```

2. **Виртуальное окружение**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Установка зависимостей**
   ```bash
   pip install -r requirements.txt
   ```

## Установка через Docker (Рекомендуется)

Самый простой способ запустить TerraData — использовать Docker Compose, который автоматически обрабатывает системные зависимости (такие как `wkhtmltopdf`).

```bash
docker-compose up --build
```

API будет доступно по адресу `http://localhost:8000`.

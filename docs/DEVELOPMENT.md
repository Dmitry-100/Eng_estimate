# Разработка и сопровождение

## Локальный запуск

```bash
pip install -r requirements.txt
python3 app.py
```

Приложение запускается на `http://127.0.0.1:5000`.

## Windows build

Сборка standalone `.exe` выполняется на Windows через PyInstaller:

```bash
pip install -r requirements-windows-build.txt
pyinstaller --clean EngEstimate.spec
```

или через готовые скрипты:

```bat
scripts\build_windows.bat
```

```powershell
.\scripts\build_windows.ps1
```

Итоговый файл:

```text
dist\EngEstimate.exe
```

Сборка настроена в оконном режиме без консоли и использует встроенное webview.

## Тесты

```bash
python3 -m unittest discover -s tests
python3 -m py_compile app.py eng_efficiency/*.py
```

Текущие тесты проверяют:

- совпадение `PLAN` с эталонным значением workbook;
- совпадение `FACT` с эталонным значением workbook;
- базовый API flow создания проекта и расчета `PLAN`.

## Правила изменения кода

### Если меняется UI

Изменять:

- `templates/index.html`
- `static/js/script.js`
- `static/css/styles.css`

Избегать:

- переноса бизнес-логики в браузер;
- дублирования расчетных правил на фронтенде.

### Если меняется модель workbook

Изменять:

- `eng_efficiency/workbook.py`
- при необходимости `eng_efficiency/calculator.py`

Обязательно:

- проверить контрольные значения;
- обновить тесты;
- обновить `docs/CALCULATION_MODEL.md`.

### Если меняется хранение данных

Изменять:

- `eng_efficiency/storage.py`
- при необходимости `eng_efficiency/statistics.py`

Рекомендуемый следующий шаг зрелости - SQLite вместо JSON, но с сохранением той же внешней логики API.

## Формат хранения проекта

Сейчас используется файл:

```text
data/projects.json
```

Он хранит:

- метаданные проекта;
- `plan_inputs`;
- `plan_result`;
- `fact_inputs`;
- `fact_result`;
- `created_at`;
- `updated_at`.

## Что развивать дальше

### Архитектура

- отделить HTTP слой в отдельный пакет;
- ввести repository interface;
- перейти на SQLite;
- добавить экспорт нормализованной workbook-модели в JSON.

### Windows delivery

- добавить icon и version metadata для `.exe`;
- сделать более дружелюбный shutdown flow внутри окна;
- при необходимости добавить installer и code signing.

### Качество

- добавить больше API тестов;
- покрыть статистические фильтры;
- добавить тесты на ошибочные сценарии пользователя;
- добавить snapshot tests для workbook extraction.

### Продукт

- добавить сравнение `PLAN` и `FACT` в одном представлении;
- добавить экспорт карточки проекта;
- добавить историю пересчетов;
- добавить более подробные справки по факторам и показателям.

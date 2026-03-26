# Engineering Efficiency Measurement

Веб-приложение на Flask для оценки эффективности инжиниринга по проектам на основе файла `Engineering Efficiency Measurement.xlsx`.

## Что делает приложение

- хранит список проектов и их метаданные;
- поддерживает два режима оценки: `PLAN` и `FACT`;
- берет структуру факторов, границы и веса прямо из Excel-модели;
- считает итоговый `PLAN`-индекс по логике листа `engineering efficiency PLAN`;
- считает итоговый `FACT`-индекс по логике листа `engineering efficiency FACT`;
- показывает статистику по группе проектов, периоду и специалисту.

## Основной сценарий

1. Пользователь создает или открывает проект.
2. Заполняет карточку проекта:
   - наименование;
   - код;
   - группа;
   - стадия;
   - даты начала и окончания;
   - руководитель проекта;
   - ГИП;
   - ответственный за проектирование.
3. На вкладке `PLAN` выбирает качественные оценки факторов.
4. Приложение автоматически подставляет числовые значения и считает итоговый показатель.
5. На вкладке `FACT` вводит фактические достигнутые значения.
6. На вкладке `Статистика` фильтрует сохраненные проекты и смотрит агрегированные значения.

## Запуск

```bash
pip install -r requirements.txt
python3 app.py
```

После запуска приложение доступно по адресу [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Windows `.exe`

Для Windows добавлен отдельный desktop entrypoint:

- [desktop_app.py](/Users/Sotnikov/Google%20Drive%20100/10%20-%20coding%20project/Eng_estimate/desktop_app.py)
- [EngEstimate.spec](/Users/Sotnikov/Google%20Drive%20100/10%20-%20coding%20project/Eng_estimate/EngEstimate.spec)
- [requirements-windows-build.txt](/Users/Sotnikov/Google%20Drive%20100/10%20-%20coding%20project/Eng_estimate/requirements-windows-build.txt)
- [scripts/build_windows.bat](/Users/Sotnikov/Google%20Drive%20100/10%20-%20coding%20project/Eng_estimate/scripts/build_windows.bat)
- [scripts/build_windows.ps1](/Users/Sotnikov/Google%20Drive%20100/10%20-%20coding%20project/Eng_estimate/scripts/build_windows.ps1)

Ожидаемый сценарий:

1. На Windows-машине установить зависимости сборки.
2. Собрать приложение через PyInstaller.
3. Получить `dist/EngEstimate.exe`.
4. Запускать `EngEstimate.exe` как обычное desktop-приложение.

При запуске `.exe` приложение:

- поднимает локальный сервер на свободном порту;
- открывает встроенное desktop-окно через webview;
- хранит пользовательские данные отдельно от bundled-файлов.

На Windows сохраненные проекты лежат в `%APPDATA%\\EngEstimate\\projects.json`.

## Структура

```text
app.py                    Flask entrypoint and API
desktop_app.py            Windows-friendly desktop EXE entrypoint
EngEstimate.spec          PyInstaller spec for Windows build
eng_efficiency/
  workbook.py             XLSX parser and model extraction
  calculator.py           PLAN / FACT calculations
  storage.py              Local JSON project storage
  statistics.py           Aggregation and filtering
  runtime.py              Runtime paths for local/frozen execution
data/projects.json        Saved projects
templates/index.html      UI shell
static/css/styles.css     UI styles
static/js/script.js       Frontend logic
scripts/build_windows.*   Windows build scripts
```

## API

- `GET /api/config` - вернуть модель факторов и показателей, извлеченную из Excel.
- `GET /api/projects` - вернуть список проектов.
- `GET /api/projects/<id>` - вернуть один проект.
- `POST /api/projects` - создать или обновить проект.
- `POST /api/projects/<id>/plan` - пересчитать и сохранить `PLAN`.
- `POST /api/projects/<id>/fact` - пересчитать и сохранить `FACT`.
- `GET /api/statistics` - получить статистику по фильтрам `project_group`, `specialist`, `date_from`, `date_to`.

## Ограничения

- хранение локальное, без базы данных;
- нет авторизации и многопользовательского режима;
- интерфейс не пытается повторить Excel 1-в-1;
- приложение ориентировано на MVP и локальную эксплуатацию.

## Подробная документация

Подробные материалы лежат в каталоге `docs/`:

- `docs/README.md` - индекс документации;
- `docs/PROJECT_OVERVIEW.md` - обзор продукта;
- `docs/ARCHITECTURE.md` - архитектура;
- `docs/API.md` - API;
- `docs/CALCULATION_MODEL.md` - расчетная модель;
- `docs/DEVELOPMENT.md` - разработка и сопровождение.
- `docs/WINDOWS_EXE.md` - сборка и запуск Windows `.exe`.

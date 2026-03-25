# Текущая и целевая архитектура

## Зачем нужен этот документ

Этот файл фиксирует разницу между:

- текущей архитектурой проекта, которая уже работает как MVP;
- целевой архитектурой, которая лучше подходит для дальнейшего роста, тестируемости и замены инфраструктурных деталей.

Текущая архитектура не является ошибочной. Она просто промежуточная: достаточно хорошая для запуска, но еще не оптимальная для долгой эволюции.

## Краткий вывод

Сейчас проект уже отделил:

- парсинг Excel;
- расчетную логику;
- storage;
- статистику;
- UI.

Но пока не отделил:

- доменную модель;
- сервисный orchestration слой;
- repository interface;
- выделенный API package;
- нормализованную модель workbook как отдельный versioned artifact.

## Текущая структура

```text
app.py
eng_efficiency/
  workbook.py
  calculator.py
  storage.py
  statistics.py
data/
  projects.json
templates/
  index.html
static/
  css/styles.css
  js/script.js
tests/
  test_app.py
docs/
  ...
```

## Что означает текущая структура

### Плюсы

- Простая точка входа.
- Легко запускать и отлаживать локально.
- Расчетная логика уже вынесена из UI.
- Workbook parsing не смешан с frontend.
- Есть выделенный слой локального хранения.
- Есть отдельный модуль статистики.

### Минусы

- `app.py` одновременно играет роль app factory, API entrypoint и orchestration слоя.
- Доменные сущности выражены в виде `dict`, а не явных моделей.
- Хранилище и его контракт не абстрагированы интерфейсом.
- API не отделен от инициализации приложения.
- Нет отдельного “application/service layer”.
- Модель workbook извлекается напрямую в runtime, а не публикуется как нормализованный JSON-spec.

## Целевая структура

Ниже структура, к которой я бы вел проект следующим этапом.

```text
app/
  api/
    routes/
    schemas/
    app_factory.py
  domain/
    entities.py
    value_objects.py
    errors.py
  services/
    project_service.py
    plan_service.py
    fact_service.py
    statistics_service.py
  repositories/
    base.py
    json_repository.py
    sqlite_repository.py
  model/
    workbook_loader.py
    workbook_spec.py
    workbook_export.py
  web/
    templates/
    static/
tests/
data/
docs/
```

## Сравнение по слоям

## 1. Входной HTTP слой

### Сейчас

- Все роуты живут в `app.py`.
- В `app.py` же живут загрузка workbook и создание storage.

### Цель

- Вынести API в `app/api/`.
- Оставить в app factory только сборку зависимостей.
- Разнести:
  - app creation;
  - route registration;
  - request/response mapping.

### Почему это важно

- проще тестировать endpoints отдельно;
- проще подключить другую реализацию frontend;
- легче расти без превращения `app.py` в большой координационный файл.

## 2. Доменный слой

### Сейчас

- Проект, результаты `PLAN`, результаты `FACT` и статистические записи представлены в виде словарей.

### Цель

Ввести явные модели:

- `Project`
- `ProjectMeta`
- `PlanAssessment`
- `FactAssessment`
- `StatisticsQuery`
- `StatisticsReport`

### Почему это важно

- меньше неявных полей;
- меньше ошибок на ключах словаря;
- легче типизировать;
- проще валидировать инварианты.

## 3. Сервисный слой

### Сейчас

- orchestration частично лежит в `app.py`;
- вычисления лежат в `calculator.py`;
- статистика лежит в `statistics.py`.

### Цель

Ввести сервисы:

- `ProjectService`
- `PlanService`
- `FactService`
- `StatisticsService`

### Почему это важно

Сервисный слой должен отвечать на вопросы:

- что происходит при сохранении проекта;
- что происходит при расчете `PLAN`;
- когда результат сохраняется;
- как собирать ответ API.

Сейчас эти шаги частично размазаны между Flask-роутами и утилитарными функциями.

## 4. Репозитории

### Сейчас

- Есть одна конкретная реализация в `storage.py` на JSON.

### Цель

Сделать:

- `ProjectRepository` как интерфейс;
- `JsonProjectRepository` как текущую реализацию;
- позже `SqliteProjectRepository`.

### Почему это важно

- можно сменить storage без переписывания API и сервисов;
- можно отдельно тестировать бизнес-логику;
- проще мигрировать с JSON на SQLite.

## 5. Модель workbook

### Сейчас

- `.xlsx` читается на старте;
- из него строится `WorkbookModel`;
- эта модель существует только в памяти процесса.

### Цель

Добавить слой `model/`, в котором:

- workbook читается;
- превращается в нормализованный spec;
- при необходимости экспортируется в JSON.

Например:

```text
model/
  workbook_loader.py
  workbook_spec.py
  workbook_export.py
data/
  workbook_spec.json
```

### Почему это важно

- появляется versioned contract модели;
- легче сравнивать изменения workbook;
- проще писать snapshot tests;
- runtime меньше зависит от деталей исходного Excel XML.

## 6. UI слой

### Сейчас

- UI построен на Flask templates + static JS/CSS.

### Цель

Для текущего масштаба можно оставить тот же подход, но структурно вынести его в `web/`:

```text
web/
  templates/
  static/
```

### Почему это важно

- логически отделяется presentation layer;
- легче перейти на другой frontend без изменения доменного слоя;
- проще ориентироваться в репозитории.

## Текущее состояние против целевого

| Область | Текущее состояние | Целевое состояние |
|---|---|---|
| Entry point | `app.py` совмещает несколько ролей | app factory + API package |
| Domain model | `dict` | dataclass / typed domain entities |
| Services | частично размазаны | явный service layer |
| Repository | одна JSON-реализация | interface + несколько реализаций |
| Workbook model | runtime extraction | normalized spec + export |
| UI | templates/static в корне | выделенный presentation layer |
| Storage | JSON | JSON сейчас, SQLite позже |

## Что уже хорошо и не требует отката

Важно: текущую архитектуру не нужно “ломать и переписывать с нуля”. В ней уже есть правильные решения:

- workbook parsing отдельно;
- calculator отдельно;
- statistics отдельно;
- storage отдельно;
- тесты на контрольные значения workbook.

То есть проект уже стоит на хорошем фундаменте. Следующий этап - не rewrite, а controlled refactor.

## План миграции к целевой архитектуре

## Этап 1. Выделить доменные модели

Сделать typed entities без изменения API:

- `Project`
- `PlanResult`
- `FactResult`
- `StatisticsReport`

Это снизит хаос `dict`-структур.

## Этап 2. Ввести service layer

Вынести orchestration из `app.py`:

- сохранение проекта;
- расчет и сохранение `PLAN`;
- расчет и сохранение `FACT`;
- сборку статистики.

## Этап 3. Ввести repository interface

Обернуть текущий JSON storage в интерфейс.

Параллельно сохранить поведение без изменения HTTP contract.

## Этап 4. Выделить API package

Перенести роуты и request mapping из `app.py` в отдельный каталог `api/`.

## Этап 5. Ввести workbook spec export

Добавить нормализованный JSON-spec как промежуточный артефакт модели.

## Этап 6. При необходимости перейти на SQLite

Только после стабилизации domain + services + repositories.

## Практический вывод

### Если задача - быстро развивать MVP

Текущая архитектура достаточна.

### Если задача - строить устойчивый продукт

Нужно двигаться к целевой архитектуре поэтапно:

1. domain
2. services
3. repository interface
4. api package
5. workbook spec
6. sqlite

## Рекомендация

Следующий полезный шаг для этого проекта:

- не менять UI;
- не менять API contract;
- сначала ввести `domain + services`.

Это даст максимальный выигрыш в чистоте архитектуры при минимальном риске сломать рабочий MVP.

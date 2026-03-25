# HTTP API

## Общие правила

- Все API-ответы возвращаются в JSON.
- `GET /` возвращает HTML интерфейс.
- Ошибки валидации возвращаются с HTTP `400`.
- Не найденный проект возвращается с HTTP `404`.

## `GET /`

Возвращает HTML интерфейс приложения.

## `GET /api/config`

Возвращает извлеченную из Excel-модели конфигурацию.

### Ответ

```json
{
  "plan_factors": [],
  "plan_measures": [],
  "fact_measures": []
}
```

`plan_factors` используются UI для построения формы `PLAN`.

`fact_measures` используются UI для формы `FACT`.

`plan_measures` полезны для отладки и анализа модели.

## `GET /api/projects`

Возвращает краткий список проектов.

### Ответ

```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "Project A",
      "code": "PRJ-01",
      "project_group": "Pilot",
      "stage": "FEED",
      "updated_at": "2026-03-25T20:00:00+00:00",
      "plan_score": 0.532893,
      "fact_score": 0.882211
    }
  ]
}
```

## `GET /api/projects/<id>`

Возвращает полную карточку проекта.

### Ответ

```json
{
  "id": "uuid",
  "name": "Project A",
  "code": "PRJ-01",
  "project_group": "Pilot",
  "stage": "FEED",
  "start_date": "2026-03-01",
  "end_date": "2026-06-01",
  "project_manager": "Иван Иванов",
  "chief_engineer": "Петр Петров",
  "design_lead": "Анна Сидорова",
  "plan_inputs": {},
  "plan_result": null,
  "fact_inputs": {},
  "fact_result": null
}
```

## `POST /api/projects`

Создает новый проект или обновляет существующий.

### Тело запроса

```json
{
  "id": "optional-uuid",
  "name": "Project A",
  "code": "PRJ-01",
  "project_group": "Pilot",
  "stage": "FEED",
  "start_date": "2026-03-01",
  "end_date": "2026-06-01",
  "project_manager": "Иван Иванов",
  "chief_engineer": "Петр Петров",
  "design_lead": "Анна Сидорова"
}
```

### Ошибка

```json
{
  "error": "Ошибка валидации.",
  "details": [
    "Поле 'Наименование проекта' обязательно."
  ]
}
```

## `POST /api/projects/<id>/plan`

Считает и сохраняет `PLAN`.

### Тело запроса

```json
{
  "inputs": {
    "data": "level_4",
    "cad": "level_4",
    "comm": "level_4"
  }
}
```

Допускается также передавать прямые численные значения, если это нужно для тестов или миграции.

### Ответ

Возвращает обновленный проект, включая `plan_result`.

## `POST /api/projects/<id>/fact`

Считает и сохраняет `FACT`.

### Тело запроса

```json
{
  "inputs": {
    "y1": 0.03,
    "y2": 3,
    "y3": 0.06
  }
}
```

### Ответ

Возвращает обновленный проект, включая `fact_result`.

## `GET /api/statistics`

Возвращает агрегированную статистику.

### Query-параметры

- `project_group`
- `specialist`
- `date_from`
- `date_to`

Все параметры необязательны.

### Ответ

```json
{
  "filters": {
    "project_group": "Pilot",
    "specialist": "",
    "date_from": "",
    "date_to": ""
  },
  "summary": {
    "project_count": 2,
    "average_plan_score": 0.61,
    "average_fact_score": 0.78,
    "average_gap_fact_minus_plan": 0.17
  },
  "stage_distribution": [
    {
      "stage": "FEED",
      "count": 1
    }
  ],
  "projects": []
}
```

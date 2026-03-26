# Быстрый старт

## Запуск

```bash
pip install -r requirements.txt
python3 app.py
```

Приложение откроется на `http://127.0.0.1:5000`.

## Проверка

```bash
curl -s http://127.0.0.1:5000/api/config
```

Если сервер отвечает JSON-структурой с `plan_factors` и `fact_measures`, приложение поднялось корректно.

## Windows `.exe`

Если нужен standalone запуск на Windows без установленного Python, используйте сборку через PyInstaller.

Основной путь:

```powershell
pip install -r requirements-windows-build.txt
pyinstaller --clean EngEstimate.spec
```

После сборки запускается:

```text
dist\EngEstimate.exe
```

В packaged-версии приложение открывается как отдельное desktop-окно без консоли.

Подробности: `docs/WINDOWS_EXE.md`

## Что проверить руками

1. Создать новый проект и сохранить карточку.
2. На вкладке `PLAN` выбрать оценки факторов и нажать `Рассчитать PLAN`.
3. На вкладке `FACT` ввести достигнутые значения и нажать `Рассчитать FACT`.
4. На вкладке `Статистика` отфильтровать проекты по группе или специалисту.

## Остановка

Нажмите `Ctrl+C` в терминале с сервером.

## Если порт занят

Измените порт внизу `app.py` или остановите предыдущий процесс:

```bash
pkill -f "python3 app.py"
```

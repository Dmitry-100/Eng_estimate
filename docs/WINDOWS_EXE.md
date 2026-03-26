# Windows `.exe`

## Цель

Этот документ описывает, как превратить проект в standalone Windows-приложение без требования ставить Python пользователю.

Выбранный подход:

- Python backend остается внутри приложения;
- приложение упаковывается в `.exe` через PyInstaller;
- при запуске `.exe` локально поднимается сервер;
- открывается встроенное desktop-окно через `pywebview`;
- данные пользователя хранятся вне bundled-ресурсов.

## Какие файлы отвечают за Windows-сборку

- `desktop_app.py` - desktop entrypoint.
- `EngEstimate.spec` - конфигурация PyInstaller.
- `requirements-windows-build.txt` - build dependencies.
- `scripts/build_windows.bat` - batch script.
- `scripts/build_windows.ps1` - PowerShell script.

## Как работает запуск

При запуске `EngEstimate.exe`:

1. выбирается свободный локальный порт;
2. создается Flask app;
3. поднимается локальный WSGI сервер;
4. открывается встроенное desktop-окно;
5. приложение работает, пока открыто окно.

Остановка:

- закрыть окно приложения.

## Где хранятся данные

### В development

Проекты сохраняются в:

```text
data/projects.json
```

### В packaged Windows build

Проекты сохраняются в:

```text
%APPDATA%\EngEstimate\projects.json
```

Это важно, потому что bundled-файлы PyInstaller не должны использоваться как рабочее место для пользовательских данных.

## Сборка на Windows

## Вариант 1. Вручную

```powershell
pip install -r requirements-windows-build.txt
pyinstaller --clean EngEstimate.spec
```

Результат:

```text
dist\EngEstimate.exe
```

## Вариант 2. Через готовые скрипты

### Batch

```bat
scripts\build_windows.bat
```

### PowerShell

```powershell
.\scripts\build_windows.ps1
```

## Что попадает в `.exe`

PyInstaller bundle включает:

- `templates/`
- `static/`
- `Engineering Efficiency Measurement.xlsx`
- icon и version metadata для `.exe`

Этого достаточно для runtime-работы приложения.

`Текст ТЗ.docx` не требуется для исполнения и не включается в bundle.

## Проверка собранного `.exe`

После сборки на Windows стоит проверить:

1. `EngEstimate.exe` запускается без установленного Python.
2. Открывается отдельное окно приложения.
3. Доступен экран создания проекта.
4. Считается `PLAN`.
5. Считается `FACT`.
6. После перезапуска проекта остаются сохраненными.

## Ограничения текущего решения

- это не native WinUI-приложение, а desktop webview shell;
- сборка Windows `.exe` должна выполняться на Windows, а не на macOS;
- installer и code signing пока не добавлены.

## Следующие улучшения

- добавить installer;
- добавить code signing;
- добавить graceful error dialog, если webview не стартовал;
- при необходимости перейти к более глубокой desktop-интеграции.

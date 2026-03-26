@echo off
setlocal

cd /d %~dp0..

python -m pip install -r requirements-windows-build.txt
pyinstaller --clean EngEstimate.spec

echo.
echo Build complete.
echo EXE: dist\EngEstimate.exe
